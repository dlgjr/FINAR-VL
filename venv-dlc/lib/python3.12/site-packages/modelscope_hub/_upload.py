"""Internal file upload implementation.

Strict behavioral parity with the old modelscope SDK upload pipeline:
- LFS detection by suffix list + size threshold
- Upload tracker for resumable uploads (.ms_upload_cache)
- Adaptive batch sizing
- Pipeline mode: ThreadPoolExecutor uploads + ordered batch commits
- Per-file retry with exponential backoff
- Per-commit retry
- ReAct progressive retry fallback (parallel → serial → single-file)
- Upload report
"""

from __future__ import annotations

import base64
import builtins as _builtins
import fnmatch
import hashlib
import io
import json
import os
import re
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, IO, Union

from tqdm.auto import tqdm

from .constants import (
    DATASET_LFS_SUFFIX,
    DEFAULT_IGNORE_PATTERNS,
    DEFAULT_MAX_WORKERS,
    MODEL_LFS_SUFFIX,
    UPLOAD_ADAPTIVE_BATCH_SIZE,
    UPLOAD_BATCH_CONSECUTIVE_FAILURE_LIMIT,
    UPLOAD_BLOB_MAX_RETRIES,
    UPLOAD_BLOB_RETRY_BACKOFF,
    UPLOAD_BLOB_RETRY_MAX_WAIT,
    UPLOAD_BLOB_TQDM_DISABLE_THRESHOLD,
    UPLOAD_CACHE_FILE,
    UPLOAD_COMMIT_BATCH_SIZE,
    UPLOAD_COMMIT_MAX_RETRIES,
    UPLOAD_COMMIT_MAX_TOTAL_WAIT,
    UPLOAD_FAILED_FILE_MAX_RETRIES,
    UPLOAD_LEGACY_PROGRESS_FILE,
    UPLOAD_LFS_ENFORCE_THRESHOLD,
    UPLOAD_MAX_FILE_COUNT,
    UPLOAD_MAX_FILE_COUNT_IN_DIR,
    UPLOAD_MAX_FILE_SIZE,
    UPLOAD_NORMAL_FILE_SIZE_TOTAL_LIMIT,
    UPLOAD_REACT_BACKOFF_MAX_EXPONENT,
    UPLOAD_REACT_ENABLED,
    UPLOAD_REACT_MAX_DELAY,
    UPLOAD_REACT_ROUND2_BASE_DELAY,
    UPLOAD_REACT_ROUND3_FILE_DELAY,
    UPLOAD_USE_CACHE,
    UPLOAD_VALIDATE_BLOB_BATCH_SIZE,
)
from .errors import (
    FileIntegrityError,
    HubError,
    InvalidParameter,
    NetworkError,
    StorageError,
)
from .utils.file_utils import compute_hash
from .utils.logger import get_logger

if TYPE_CHECKING:
    from ._legacy_api import LegacyClient
    from ._openapi import OpenAPIClient
    from .config import HubConfig

logger = get_logger("upload")


PathOrFileObj = Union[str, Path, bytes, BinaryIO, IO[bytes]]

_TRACKER_VERSION = 3


# ====================================================================
# Helpers
# ====================================================================


class _CountedReadStream:
    """File wrapper that counts bytes read and updates a progress bar."""

    def __init__(self, file_obj: Any, expected_size: int,
                 pbar: Any, chunk_size: int) -> None:
        self._file = file_obj
        self._expected_size = expected_size
        self._pbar = pbar
        self._chunk_size = chunk_size
        self._bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        read_size = self._chunk_size if size < 0 else min(size, self._chunk_size)
        chunk = self._file.read(read_size)
        if chunk:
            n = len(chunk)
            self._bytes_read += n
            self._pbar.update(n)
        return chunk

    @property
    def bytes_read(self) -> int:
        return self._bytes_read

    def verify_complete(self) -> None:
        if self._bytes_read != self._expected_size:
            raise FileIntegrityError(
                f"Upload data incomplete: read {self._bytes_read} bytes, "
                f"expected {self._expected_size} bytes. "
                f"File may have been modified during upload."
            )


def _is_lfs(path: str | Path, size: int, repo_type: str) -> bool:
    """Determine if a file should use LFS upload mode (suffix + size threshold)."""
    if size > UPLOAD_LFS_ENFORCE_THRESHOLD:
        return True
    suffix = Path(path).suffix.lower() if isinstance(path, (str, Path)) else ""
    if repo_type == "model":
        return suffix in MODEL_LFS_SUFFIX
    if repo_type == "dataset":
        return suffix in DATASET_LFS_SUFFIX
    return size > UPLOAD_LFS_ENFORCE_THRESHOLD


def _upload_mode(path: str | Path, size: int, repo_type: str) -> str:
    """Return the commit/upload mode for a file."""
    return "lfs" if _is_lfs(path, size, repo_type) else "normal"


def _calculate_adaptive_batch_size(total_files: int) -> int:
    """Calculate optimal commit batch size based on total file count."""
    if total_files <= 0:
        return 1
    if total_files <= 100:
        return total_files
    if total_files <= 10_000:
        return max(64, min(256, total_files // 80))
    return 512


def _compute_file_hash(
    file_path_or_obj: str | Path | bytes | BinaryIO | IO[bytes],
    buffer_size_mb: int = 16,
) -> dict:
    """Compute SHA256 hash and size for a file, bytes, or file-like object.

    Returns dict with 'file_hash', 'file_size', 'file_path_or_obj' keys.
    """
    if isinstance(file_path_or_obj, bytes):
        return {
            "file_path_or_obj": file_path_or_obj,
            "file_hash": hashlib.sha256(file_path_or_obj).hexdigest(),
            "file_size": len(file_path_or_obj),
        }
    if isinstance(file_path_or_obj, (str, Path)):
        path = Path(file_path_or_obj)
        file_size = path.stat().st_size
        file_hash = compute_hash(path, "sha256")
        return {
            "file_path_or_obj": str(file_path_or_obj),
            "file_hash": file_hash,
            "file_size": file_size,
        }
    # BinaryIO / file-like object: read into bytes
    data = file_path_or_obj.read()
    return {
        "file_path_or_obj": data,
        "file_hash": hashlib.sha256(data).hexdigest(),
        "file_size": len(data),
    }


def _matches_patterns(path: str, patterns: list[str] | None) -> bool:
    if not patterns:
        return False
    return any(fnmatch.fnmatch(path, pat) for pat in patterns)


def _filter_repo_objects(
    items: list[str],
    allow_patterns: list[str] | None = None,
    ignore_patterns: list[str] | None = None,
) -> list[str]:
    """Filter file paths using fnmatch allow/ignore pattern lists."""
    filtered = []
    for item in items:
        if allow_patterns and not _matches_patterns(item, allow_patterns):
            continue
        if ignore_patterns and _matches_patterns(item, ignore_patterns):
            continue
        filtered.append(item)
    return filtered


class _ErrorCategory:
    TRANSIENT_NETWORK = "transient_network"
    TRANSIENT_SERVER = "transient_server"
    THROTTLED = "throttled"
    AUTH_FAILED = "auth_failed"
    NOT_FOUND = "not_found"
    FILE_INVALID = "file_invalid"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"

    _NON_RETRYABLE = {"auth_failed", "not_found", "file_invalid", "permanent"}

    @classmethod
    def is_retryable(cls, category: str) -> bool:
        return category not in cls._NON_RETRYABLE


_CATEGORY_BY_ERROR_CODE: dict[str, str] = {
    "E1001": _ErrorCategory.TRANSIENT_NETWORK,   # timeout
    "E1002": _ErrorCategory.TRANSIENT_SERVER,     # server error
    "E1003": _ErrorCategory.TRANSIENT_SERVER,     # storage error
    "E1020": _ErrorCategory.TRANSIENT_NETWORK,    # network/connection error
    "E1021": _ErrorCategory.THROTTLED,            # rate limit
    "E1022": _ErrorCategory.FILE_INVALID,         # cache error
    "E2020": _ErrorCategory.TRANSIENT_SERVER,     # file integrity (auto-retry)
    "E3001": _ErrorCategory.AUTH_FAILED,          # authentication
    "E3002": _ErrorCategory.AUTH_FAILED,          # permission
    "E3020": _ErrorCategory.NOT_FOUND,            # not exist
    "E3021": _ErrorCategory.FILE_INVALID,         # invalid parameter
    "E3023": _ErrorCategory.FILE_INVALID,         # not supported
    "E9001": _ErrorCategory.UNKNOWN,              # unknown/fallback
}


def classify_error(error: Exception) -> str:
    """Classify an exception for retry strategy using the SDK error hierarchy.

    For :class:`HubError` instances, classification is driven by
    :attr:`~HubError.error_code` via a lookup table — no ``isinstance``
    chains or string-matching heuristics needed for known error types.
    """
    if isinstance(error, HubError):
        code = getattr(error, "error_code", None)
        if code and code in _CATEGORY_BY_ERROR_CODE:
            return _CATEGORY_BY_ERROR_CODE[code]
        return _ErrorCategory.UNKNOWN if error.retryable else _ErrorCategory.PERMANENT

    if isinstance(error, FileNotFoundError):
        return _ErrorCategory.FILE_INVALID
    if isinstance(error, _builtins.PermissionError):
        return _ErrorCategory.FILE_INVALID
    if isinstance(error, (ConnectionError, TimeoutError)):
        return _ErrorCategory.TRANSIENT_NETWORK
    if isinstance(error, (IOError, OSError)):
        error_str = str(error).lower()
        if "size changed" in error_str or "no such file" in error_str:
            return _ErrorCategory.FILE_INVALID
        if "permission" in error_str or "access denied" in error_str:
            return _ErrorCategory.FILE_INVALID
        return _ErrorCategory.TRANSIENT_NETWORK

    return _ErrorCategory.UNKNOWN


# ====================================================================
# Upload Tracker
# ====================================================================


class FileStatus:
    UPLOADED = "u"
    COMMITTED = "c"
    FAILED = "f"


class UploadTracker:
    """Persistent JSON cache at {folder}/.ms_upload_cache for resumable uploads."""

    def __init__(self, cache_path: str | Path, repo_id: str) -> None:
        self._path = Path(cache_path)
        self._repo_id = repo_id
        self._files: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._dirty = False
        self._load()

    @staticmethod
    def _make_key(rel_path: str, mtime: float, size: int) -> str:
        return f"{rel_path}|{mtime}|{size}"

    def get_hash(self, rel_path: str, mtime: float, size: int) -> dict | None:
        key = self._make_key(rel_path, mtime, size)
        with self._lock:
            entry = self._files.get(key)
        if entry is None or "hash" not in entry:
            return None
        return {
            "file_path_or_obj": rel_path,
            "file_hash": entry["hash"],
            "file_size": entry["size"],
        }

    def put_hash(self, rel_path: str, mtime: float, size: int,
                 hash_info: dict) -> None:
        key = self._make_key(rel_path, mtime, size)
        with self._lock:
            entry = self._files.get(key, {})
            entry["hash"] = hash_info["file_hash"]
            entry["size"] = hash_info["file_size"]
            self._files[key] = entry
            self._dirty = True

    def is_committed(self, rel_path: str, mtime: float, size: int) -> bool:
        key = self._make_key(rel_path, mtime, size)
        with self._lock:
            entry = self._files.get(key)
        return entry is not None and entry.get("status") == FileStatus.COMMITTED

    def get_status(self, rel_path: str, mtime: float, size: int) -> str | None:
        key = self._make_key(rel_path, mtime, size)
        with self._lock:
            entry = self._files.get(key)
        return entry.get("status") if entry else None

    def mark_uploaded(self, rel_path: str, mtime: float, size: int) -> None:
        key = self._make_key(rel_path, mtime, size)
        with self._lock:
            if key in self._files:
                self._files[key]["status"] = FileStatus.UPLOADED
                self._dirty = True

    def mark_committed_batch(
        self, file_keys: list[tuple[str, float, int]]
    ) -> None:
        with self._lock:
            for rel_path, mtime, size in file_keys:
                key = self._make_key(rel_path, mtime, size)
                if key in self._files:
                    self._files[key]["status"] = FileStatus.COMMITTED
            self._dirty = True

    def mark_failed(self, rel_path: str, mtime: float, size: int,
                    error_type: str = "") -> None:
        key = self._make_key(rel_path, mtime, size)
        with self._lock:
            if key in self._files:
                self._files[key]["status"] = FileStatus.FAILED
                if error_type:
                    self._files[key]["error_type"] = error_type
            else:
                entry: dict[str, Any] = {"status": FileStatus.FAILED}
                if error_type:
                    entry["error_type"] = error_type
                self._files[key] = entry
            self._dirty = True

    def save(self) -> None:
        with self._lock:
            if not self._dirty:
                return
            data = {
                "version": _TRACKER_VERSION,
                "repo_id": self._repo_id,
                "files": {k: dict(v) for k, v in self._files.items()},
            }
            self._dirty = False
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=str(self._path.parent), suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                os.replace(tmp_path, str(self._path))
            except BaseException:
                os.unlink(tmp_path)
                raise
        except Exception as e:
            logger.warning("Failed to save upload tracker: %s", e)

    def clear(self) -> None:
        try:
            self._path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning("Failed to delete tracker file: %s", e)
        with self._lock:
            self._files.clear()
            self._dirty = False

    def _load(self) -> None:
        if not self._path.exists():
            self._check_legacy_progress()
            return
        try:
            with open(self._path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load upload tracker, starting fresh: %s", e)
            return

        version = data.get("version")
        if version is None:
            self._migrate_v1(data)
            return

        stored_repo = data.get("repo_id", "")
        if stored_repo and stored_repo != self._repo_id:
            logger.warning(
                "Tracker repo_id mismatch (cached: %s, current: %s), "
                "ignoring stale tracker.",
                stored_repo, self._repo_id,
            )
            return

        self._files = data.get("files", {})
        committed_count = sum(
            1 for e in self._files.values()
            if e.get("status") == FileStatus.COMMITTED
        )
        if committed_count > 0:
            logger.info(
                "Upload tracker loaded: %d entries, %d committed.",
                len(self._files), committed_count,
            )
        self._check_legacy_progress()

    def _migrate_v1(self, data: dict) -> None:
        migrated = {}
        for key, value in data.items():
            if isinstance(value, dict) and "file_hash" in value:
                migrated[key] = {
                    "hash": value["file_hash"],
                    "size": value.get("file_size", 0),
                }
        self._files = migrated
        self._dirty = True
        if migrated:
            logger.info(
                "Migrated %d entries from legacy hash cache format.",
                len(migrated),
            )

    def _check_legacy_progress(self) -> None:
        legacy_path = self._path.parent / UPLOAD_LEGACY_PROGRESS_FILE
        if legacy_path.exists():
            logger.warning(
                "Legacy upload progress file detected: %s. "
                "This file is no longer used. You may delete it safely.",
                legacy_path,
            )


class NullTracker:
    """No-op tracker for when caching is disabled."""

    def get_hash(self, rel_path: str, mtime: float, size: int) -> None:
        return None

    def put_hash(self, rel_path: str, mtime: float, size: int,
                 hash_info: dict) -> None:
        pass

    def is_committed(self, rel_path: str, mtime: float, size: int) -> bool:
        return False

    def get_status(self, rel_path: str, mtime: float, size: int) -> None:
        return None

    def mark_uploaded(self, rel_path: str, mtime: float, size: int) -> None:
        pass

    def mark_committed_batch(self, file_keys: list) -> None:
        pass

    def mark_failed(self, rel_path: str, mtime: float, size: int,
                    error_type: str = "") -> None:
        pass

    def save(self) -> None:
        pass

    def clear(self) -> None:
        pass


# ====================================================================
# Batch Tracker
# ====================================================================


class BatchTracker:
    """Thread-safe tracker for pre-assigned upload batches."""

    def __init__(self, total_files: int, batch_size: int) -> None:
        self._batch_size = batch_size
        self._num_batches = (
            (total_files - 1) // batch_size + 1 if total_files > 0 else 0
        )
        self._batch_results: list[list[dict]] = [
            [] for _ in range(self._num_batches)
        ]
        self._batch_failures: list[list[tuple]] = [
            [] for _ in range(self._num_batches)
        ]
        self._batch_expected: list[int] = []
        for i in range(self._num_batches):
            start = i * batch_size
            end = min(start + batch_size, total_files)
            self._batch_expected.append(end - start)
        self._batch_events: list[threading.Event] = [
            threading.Event() for _ in range(self._num_batches)
        ]
        self._lock = threading.Lock()

    @property
    def num_batches(self) -> int:
        return self._num_batches

    def batch_index(self, file_index: int) -> int:
        return file_index // self._batch_size

    def record_success(self, file_index: int, result: dict) -> None:
        idx = self.batch_index(file_index)
        with self._lock:
            self._batch_results[idx].append(result)
            if self._is_batch_complete(idx):
                self._batch_events[idx].set()

    def record_failure(self, file_index: int, item: tuple,
                       error: Exception) -> None:
        idx = self.batch_index(file_index)
        with self._lock:
            self._batch_failures[idx].append((item, error))
            if self._is_batch_complete(idx):
                self._batch_events[idx].set()

    def mark_file_skipped(self, file_index: int) -> None:
        idx = self.batch_index(file_index)
        with self._lock:
            self._batch_expected[idx] -= 1
            if self._is_batch_complete(idx):
                self._batch_events[idx].set()

    def wait_for_batch(
        self, batch_idx: int
    ) -> tuple[list[dict], list[tuple]]:
        self._batch_events[batch_idx].wait()
        with self._lock:
            return (
                list(self._batch_results[batch_idx]),
                list(self._batch_failures[batch_idx]),
            )

    def _is_batch_complete(self, batch_idx: int) -> bool:
        count = (
            len(self._batch_results[batch_idx])
            + len(self._batch_failures[batch_idx])
        )
        return count >= self._batch_expected[batch_idx]


# ====================================================================
# Upload Manager
# ====================================================================


class UploadManager:
    """Internal file upload implementation with production-grade retry and resume."""

    def __init__(
        self,
        legacy_client: "LegacyClient",
        config: "HubConfig",
        openapi_client: "OpenAPIClient | None" = None,
        *,
        create_repo_fn: Any = None,
    ) -> None:
        self._client = legacy_client
        self._config = config
        self._openapi = openapi_client
        self._create_repo_fn = create_repo_fn

    # ------------------------------------------------------------------
    # Public: upload_file
    # ------------------------------------------------------------------
    def upload_file(
        self,
        repo_id: str,
        repo_type: str,
        path_or_fileobj: PathOrFileObj,
        path_in_repo: str,
        *,
        commit_message: str = "Upload file",
        commit_description: str | None = None,
        revision: str = "master",
        buffer_size_mb: int = 16,
        disable_tqdm: bool = False,
    ) -> dict:
        """Upload a single file to a repository."""
        if path_or_fileobj is None:
            raise InvalidParameter("Path or file object cannot be None!")

        if isinstance(path_or_fileobj, (str, Path)):
            path_or_fileobj = os.path.abspath(
                os.path.expanduser(str(path_or_fileobj))
            )
            path_in_repo = path_in_repo or os.path.basename(path_or_fileobj)
        else:
            if not path_in_repo:
                raise InvalidParameter("Arg `path_in_repo` cannot be empty!")

        hash_info = _compute_file_hash(path_or_fileobj, buffer_size_mb)
        file_hash = hash_info["file_hash"]
        file_size = hash_info["file_size"]
        # If BinaryIO was consumed, _compute_file_hash returns the bytes
        if not isinstance(path_or_fileobj, (str, Path, bytes)):
            path_or_fileobj = hash_info["file_path_or_obj"]

        commit_message = commit_message or f"Upload {path_in_repo} to ModelScope hub"

        if self._create_repo_fn is not None:
            self._create_repo_fn(repo_id, repo_type)

        upload_mode = _upload_mode(path_in_repo, file_size, repo_type)
        if upload_mode == "lfs":
            upload_res = self._upload_blob(
                repo_id=repo_id,
                repo_type=repo_type,
                sha256=file_hash,
                size=file_size,
                data=path_or_fileobj,
                disable_tqdm=disable_tqdm,
                tqdm_desc=f"[Uploading] {path_in_repo}",
                buffer_size_mb=buffer_size_mb,
            )
        else:
            upload_res = {
                "url": None,
                "is_uploaded": True,
                "is_reused": False,
                "is_blob_uploaded": False,
            }

        operation = self._build_operation(
            path_in_repo=path_in_repo,
            path_or_fileobj=path_or_fileobj,
            hash_info=hash_info,
            upload_mode=upload_mode,
            is_uploaded=upload_res["is_uploaded"],
        )

        print(f"Committing file to {repo_id} ...", flush=True)
        return self._client.create_commit(
            repo_id=repo_id,
            repo_type=repo_type,
            operations=[operation],
            commit_message=commit_message,
            revision=revision,
        )

    # ------------------------------------------------------------------
    # Public: upload_folder
    # ------------------------------------------------------------------
    def upload_folder(
        self,
        repo_id: str,
        repo_type: str,
        folder_path: str | Path,
        *,
        path_in_repo: str = "",
        commit_message: str | None = None,
        commit_description: str | None = None,
        revision: str = "master",
        allow_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        max_workers: int | None = None,
        use_cache: bool = UPLOAD_USE_CACHE,
        disable_tqdm: bool = False,
        sync_remote_repo: bool = False,
    ) -> dict | list[dict] | None:
        """Upload a folder with resumable support, adaptive batching, and retry."""
        start_time = time.time()

        if not repo_id:
            raise InvalidParameter("The arg `repo_id` cannot be empty!")
        if folder_path is None:
            raise InvalidParameter("The arg `folder_path` cannot be None!")

        if max_workers is None:
            max_workers = DEFAULT_MAX_WORKERS

        # Normalize patterns
        allow_patterns = allow_patterns or None
        if ignore_patterns is None:
            ignore_patterns = []
        elif isinstance(ignore_patterns, str):
            ignore_patterns = [ignore_patterns]
        else:
            ignore_patterns = list(ignore_patterns)
        ignore_patterns += DEFAULT_IGNORE_PATTERNS

        if allow_patterns is not None:
            ignore_patterns = [
                p for p in ignore_patterns if p not in allow_patterns
            ]

        commit_message = (
            commit_message
            if commit_message is not None
            else f"Upload to {repo_id} on ModelScope hub"
        )
        commit_description = commit_description or "Uploading files"

        # Exclude internal cache files from upload
        _internal_files = [UPLOAD_CACHE_FILE, UPLOAD_LEGACY_PROGRESS_FILE]
        _internal_ignore = [p for f in _internal_files for p in (f, f"*/{f}")]
        ignore_patterns = ignore_patterns + _internal_ignore

        # Collect files
        logger.info("Preparing files to upload ...")
        sorted_files = self._prepare_upload_folder(
            folder_path=folder_path,
            path_in_repo=path_in_repo,
            repo_type=repo_type,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
        )

        # For sync mode: collect ALL local files (unfiltered) to avoid
        # treating pattern-excluded files as remote orphans.
        if sync_remote_repo:
            all_local_files_in_repo = self._prepare_upload_folder(
                folder_path=folder_path,
                path_in_repo=path_in_repo,
                repo_type=repo_type,
                allow_patterns=None,
                ignore_patterns=None,
            )
            all_local_paths_in_repo = {p for p, _ in all_local_files_in_repo}
        else:
            all_local_paths_in_repo = set()

        if not sorted_files:
            raise InvalidParameter(f"No files to upload in the folder: {folder_path} !")

        logger.info("Checking %d files to upload ...", len(sorted_files))

        if self._create_repo_fn is not None:
            self._create_repo_fn(repo_id, repo_type)

        # Sort for deterministic batch assignment
        sorted_files = sorted(sorted_files, key=lambda x: x[0])

        # Calculate batch size
        if UPLOAD_ADAPTIVE_BATCH_SIZE:
            commit_batch_size = _calculate_adaptive_batch_size(len(sorted_files))
            logger.info(
                "Adaptive batch size: %d (for %d files)",
                commit_batch_size, len(sorted_files),
            )
        else:
            commit_batch_size = (
                UPLOAD_COMMIT_BATCH_SIZE
                if UPLOAD_COMMIT_BATCH_SIZE > 0
                else len(sorted_files)
            )

        # Initialize tracker
        folder_path_resolved = Path(folder_path).resolve()
        if use_cache:
            cache_path = folder_path_resolved / UPLOAD_CACHE_FILE
            tracker: UploadTracker | NullTracker = UploadTracker(
                cache_path, repo_id=repo_id
            )
        else:
            tracker = NullTracker()
        batch_tracker = BatchTracker(len(sorted_files), commit_batch_size)

        # Skip individually committed files
        files_to_upload: list[tuple[int, tuple[str, str]]] = []
        skipped_indices: set[int] = set()
        for file_idx, (file_path_in_repo, file_path) in enumerate(sorted_files):
            try:
                st = os.stat(file_path)
                if tracker.is_committed(
                    file_path_in_repo, st.st_mtime, st.st_size
                ):
                    skipped_indices.add(file_idx)
                    batch_tracker.mark_file_skipped(file_idx)
                    continue
            except OSError as e:
                logger.warning(
                    "Cannot stat file %s, will re-upload: %s",
                    file_path_in_repo, e,
                )
            files_to_upload.append(
                (file_idx, (file_path_in_repo, file_path))
            )

        # Batch pre-validation for LFS files with cached hashes
        pre_validated_map: dict[str, str | None] = {}
        lfs_hash_info_map: dict[int, tuple[dict, os.stat_result]] = {}

        for file_idx, (file_path_in_repo, file_path) in files_to_upload:
            try:
                st = os.stat(file_path)
                cached = tracker.get_hash(
                    file_path_in_repo, st.st_mtime, st.st_size
                )
                if cached is not None:
                    if (
                        _upload_mode(
                            file_path_in_repo, cached["file_size"], repo_type,
                        ) == "lfs"
                    ):
                        lfs_hash_info_map[file_idx] = (cached, st)
                    continue
            except OSError:
                pass

        if lfs_hash_info_map:
            objects = [
                {"oid": info["file_hash"], "size": info["file_size"]}
                for info, _ in lfs_hash_info_map.values()
            ]
            validated = self._validate_blobs_batch(
                repo_id=repo_id, repo_type=repo_type, objects=objects
            )
            pre_validated_map = validated
            reused = sum(1 for v in validated.values() if v is None)
            logger.info(
                "Pre-validated %d cached LFS hash(es): %d globally existing, "
                "%d need upload.",
                len(objects), reused, len(objects) - reused,
            )

        skipped_count = len(skipped_indices)
        if skipped_count > 0:
            logger.info("%d file(s) already committed, skipping.", skipped_count)

        logger.info(
            "Scan complete: %d total, %d committed (skip), %d to process.",
            len(sorted_files), skipped_count, len(files_to_upload),
        )

        logger.info(
            "Uploading %d file(s) in %d batch(es) of size %d (pipeline mode).",
            len(files_to_upload), batch_tracker.num_batches, commit_batch_size,
        )

        # Pipeline: upload workers
        def _upload_worker(
            file_idx: int, file_info: tuple, pre_validated: Any = None
        ) -> None:
            path_in_repo_w, file_path_w = file_info
            try:
                logger.debug("Uploading: %s ...", path_in_repo_w)
                result = self._upload_single_file(
                    path_in_repo_w,
                    file_path_w,
                    repo_id=repo_id,
                    repo_type=repo_type,
                    tracker=tracker,
                    pre_validated=pre_validated,
                    disable_tqdm=disable_tqdm,
                )
                logger.debug("Uploaded: %s", path_in_repo_w)
                batch_tracker.record_success(file_idx, result)
            except Exception as e:
                logger.error("Upload failed: %s - %s", path_in_repo_w, e)
                batch_tracker.record_failure(file_idx, file_info, e)

        # Pipeline: consume batches in order
        commit_infos: list[dict] = []
        all_results: list[dict] = []
        total_failed_files: list[tuple] = []
        num_batches = batch_tracker.num_batches

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for file_idx, file_info in files_to_upload:
                    pv = None
                    if file_idx in lfs_hash_info_map:
                        cached_hash = lfs_hash_info_map[file_idx][0]["file_hash"]
                        pv = pre_validated_map.get(cached_hash)
                        if pv is None:
                            pv = True
                    executor.submit(_upload_worker, file_idx, file_info, pv)

                consecutive_failures = 0
                for batch_idx in tqdm(
                    range(num_batches),
                    desc="[Committing batches]",
                    total=num_batches,
                    disable=disable_tqdm,
                ):
                    batch_start = batch_idx * commit_batch_size
                    batch_end = min(
                        batch_start + commit_batch_size, len(sorted_files)
                    )
                    if all(
                        i in skipped_indices
                        for i in range(batch_start, batch_end)
                    ):
                        logger.info(
                            "Batch %d/%d fully committed, skipping.",
                            batch_idx + 1, num_batches,
                        )
                        continue

                    results, failures = batch_tracker.wait_for_batch(batch_idx)

                    if failures:
                        total_failed_files.extend(failures)
                        for item, err in failures:
                            logger.error("  Failed: %s - %s", item[0], err)

                    self._track_uploaded_batch(tracker, results)

                    operations = self._build_batch_operations(
                        results, repo_type
                    )
                    if not operations:
                        logger.error(
                            "Batch %d/%d: all files failed, skipping commit.",
                            batch_idx + 1, num_batches,
                        )
                        continue

                    batch_commit_message = (
                        f"{commit_message} (batch {batch_idx + 1}/{num_batches})"
                    )
                    try:
                        commit_info = self._commit_with_retry(
                            repo_id=repo_id,
                            repo_type=repo_type,
                            operations=operations,
                            commit_message=batch_commit_message,
                            revision=revision,
                        )
                        commit_infos.append(commit_info)
                        all_results.extend(results)
                        logger.info(
                            "Batch %d/%d: committed %d file(s).",
                            batch_idx + 1, num_batches, len(results),
                        )
                        self._track_committed_batch(tracker, results)
                        consecutive_failures = 0
                    except Exception as e:
                        logger.error(
                            "Batch %d/%d commit failed: %s",
                            batch_idx + 1, num_batches, e,
                        )
                        category = classify_error(e)
                        if not _ErrorCategory.is_retryable(category):
                            for r in results:
                                tracker.mark_failed(
                                    r["file_path_in_repo"],
                                    r["file_mtime"],
                                    r["file_size_on_disk"],
                                    error_type="commit_" + category,
                                )
                            logger.error(
                                "Batch %d/%d: permanent failure (%s), "
                                "%d file(s) will not be retried.",
                                batch_idx + 1, num_batches,
                                category, len(results),
                            )
                            consecutive_failures += 1
                        else:
                            for r in results:
                                total_failed_files.append(
                                    (
                                        (r["file_path_in_repo"], r["file_path"]),
                                        e,
                                    )
                                )
                            logger.warning(
                                "Batch %d/%d: %d file(s) recovered to retry "
                                "queue (error_category=%s).",
                                batch_idx + 1, num_batches,
                                len(results), category,
                            )
                            consecutive_failures += 1

                        if consecutive_failures >= UPLOAD_BATCH_CONSECUTIVE_FAILURE_LIMIT:
                            raise RuntimeError(
                                f"Upload aborted: {consecutive_failures} consecutive batch commits failed. "
                                f"Last error: {e}"
                            )
        finally:
            tracker.save()

        # ReAct progressive retry fallback
        if total_failed_files and UPLOAD_REACT_ENABLED:
            total_failed_files, react_commits, react_results = (
                self._retry_failed_files_react(
                    failed_files=total_failed_files,
                    tracker=tracker,
                    repo_id=repo_id,
                    repo_type=repo_type,
                    commit_message=commit_message,
                    revision=revision,
                    max_workers=max_workers,
                    disable_tqdm=disable_tqdm,
                )
            )
            commit_infos.extend(react_commits)
            all_results.extend(react_results)
        elif total_failed_files:
            total_failed_files = self._retry_failed_simple(
                failed_files=total_failed_files,
                tracker=tracker,
                repo_id=repo_id,
                repo_type=repo_type,
                commit_message=commit_message,
                commit_description=commit_description,
                revision=revision,
                commit_infos=commit_infos,
                all_results=all_results,
                disable_tqdm=disable_tqdm,
            )

        tracker.save()

        # Sync: delete remote orphan files
        deleted_count = 0
        if sync_remote_repo and not total_failed_files:
            prefix = path_in_repo.strip("/") if path_in_repo else ""
            orphans = self._compute_remote_orphans(
                repo_id=repo_id,
                repo_type=repo_type,
                revision=revision,
                local_paths_in_repo=all_local_paths_in_repo,
                path_in_repo_prefix=prefix,
            )
            if orphans:
                delete_ops = self._build_delete_operations(orphans)
                delete_commit_message = (
                    f"{commit_message} "
                    f"(sync: delete {len(orphans)} orphan file(s))"
                )
                try:
                    delete_commit = self._commit_with_retry(
                        repo_id=repo_id,
                        repo_type=repo_type,
                        operations=delete_ops,
                        commit_message=delete_commit_message,
                        revision=revision,
                    )
                    commit_infos.append(delete_commit)
                    deleted_count = len(orphans)
                    logger.info(
                        "Sync: deleted %d orphan file(s) from remote.",
                        deleted_count,
                    )
                except Exception as e:
                    logger.error("Sync delete commit failed: %s", e)

        # Upload report
        elapsed = time.time() - start_time
        total_files = len(sorted_files)
        failed_count = len(total_failed_files)
        lfs_reused_count = sum(
            1 for r in all_results
            if r.get("upload_mode") == "lfs" and r.get("is_reused")
        )
        lfs_uploaded_count = sum(
            1 for r in all_results if r.get("is_blob_uploaded")
        )
        normal_count = sum(
            1 for r in all_results if r.get("upload_mode") == "normal"
        )
        committed_count = len(all_results)

        print("=" * 60)
        print("Upload Report")
        print("-" * 60)
        print(f"  Total files       : {total_files}")
        print(f"  Skipped (cached)  : {skipped_count}")
        print(f"  Normal committed  : {normal_count}")
        print(f"  LFS existed       : {lfs_reused_count}")
        print(f"  LFS uploaded PUT  : {lfs_uploaded_count}")
        print(f"  Failed            : {failed_count}")
        print(f"  Committed         : {committed_count}")
        print(f"  Deleted (sync)    : {deleted_count}")
        print(f"  Elapsed           : {elapsed:.1f}s")
        print("=" * 60)

        if total_failed_files:
            for (path_in_repo_f, _), err in total_failed_files:
                logger.error("  - %s: %s: %s", path_in_repo_f, type(err).__name__, err)
            succeeded = total_files - failed_count
            raise StorageError(
                f"{failed_count} file(s) failed to upload. "
                f"Please manually try again. Successfully uploaded "
                f"{succeeded} file(s) will be automatically skipped "
                f"during the retry."
            )

        if not commit_infos:
            if skipped_count == len(sorted_files):
                logger.info("All files were already committed.")
                return None
            return None

        return commit_infos[0] if len(commit_infos) == 1 else commit_infos

    # ------------------------------------------------------------------
    # Internal: remote orphan detection and deletion
    # ------------------------------------------------------------------
    def _compute_remote_orphans(
        self,
        repo_id: str,
        repo_type: str,
        revision: str,
        local_paths_in_repo: set[str],
        path_in_repo_prefix: str,
    ) -> list[str]:
        """Compute remote files that are not present locally (orphans).

        Only files under ``path_in_repo_prefix`` are considered.
        Returns a list of remote file paths to delete.
        """
        logger.info("Sync: fetching remote file list for orphan detection ...")
        raw_items = self._client.list_repo_files(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            recursive=True,
        )

        remote_paths: list[str] = []
        for item in raw_items:
            item_type = item.get("Type") or item.get("type") or "blob"
            if item_type == "tree":
                continue
            path = (
                item.get("Path") or item.get("path") or item.get("Name") or ""
            )
            if not path:
                continue
            remote_paths.append(path)

        # Filter by prefix scope
        if path_in_repo_prefix:
            scope_prefix = path_in_repo_prefix + "/"
            remote_paths = [
                p for p in remote_paths if p.startswith(scope_prefix)
            ]

        orphans = [p for p in remote_paths if p not in local_paths_in_repo]
        logger.info(
            "Sync: %d remote file(s) in scope, %d orphan(s) detected.",
            len(remote_paths), len(orphans),
        )
        return orphans

    @staticmethod
    def _build_delete_operations(orphan_paths: list[str]) -> list[dict]:
        """Build delete operations for orphan remote files."""
        return [
            {
                "action": "delete",
                "path": p,
                "type": "normal",
                "size": 0,
                "sha256": "",
                "content": "",
                "encoding": "",
            }
            for p in orphan_paths
        ]

    # ------------------------------------------------------------------
    # Internal: single file upload with retry
    # ------------------------------------------------------------------
    def _upload_single_file(
        self,
        file_path_in_repo: str,
        file_path: str,
        *,
        repo_id: str,
        repo_type: str,
        tracker: UploadTracker | NullTracker | None = None,
        pre_validated: Any = None,
        disable_tqdm: bool = False,
    ) -> dict:
        if tracker is None:
            tracker = NullTracker()
        hash_info_d = None
        file_stat = None
        is_real_path = isinstance(file_path, (str, os.PathLike))

        if is_real_path:
            try:
                file_stat = os.stat(file_path)
                cached = tracker.get_hash(
                    file_path_in_repo, file_stat.st_mtime, file_stat.st_size
                )
                if cached is not None:
                    hash_info_d = cached
                    hash_info_d["file_path_or_obj"] = file_path
            except OSError:
                file_stat = None

        if hash_info_d is None:
            hash_info_d = _compute_file_hash(file_path_or_obj=file_path)
            if is_real_path:
                try:
                    if file_stat is None:
                        file_stat = os.stat(file_path)
                    tracker.put_hash(
                        file_path_in_repo, file_stat.st_mtime,
                        file_stat.st_size, hash_info_d,
                    )
                except OSError:
                    pass

        if file_stat is None and is_real_path:
            try:
                file_stat = os.stat(file_path)
            except OSError:
                pass

        file_size: int = hash_info_d["file_size"]
        file_hash: str = hash_info_d["file_hash"]

        upload_mode = _upload_mode(file_path_in_repo, file_size, repo_type)

        if upload_mode == "lfs":
            # Retry loop for transient blob upload failures
            last_error = None
            for attempt in range(UPLOAD_BLOB_MAX_RETRIES):
                try:
                    if isinstance(file_path, (str, os.PathLike)):
                        current_size = os.path.getsize(str(file_path))
                        if current_size != file_size:
                            raise InvalidParameter(
                                f"File size changed since hash computation: "
                                f"was {file_size}, now {current_size}. "
                                f"File may have been modified: {file_path_in_repo}"
                            )
                    upload_res = self._upload_blob(
                        repo_id=repo_id,
                        repo_type=repo_type,
                        sha256=file_hash,
                        size=file_size,
                        data=file_path,
                        disable_tqdm=(
                            disable_tqdm
                            or file_size <= UPLOAD_BLOB_TQDM_DISABLE_THRESHOLD
                        ),
                        tqdm_desc=f"[Uploading {file_path_in_repo}]",
                        pre_validated=pre_validated,
                    )
                    break
                except (HubError, ConnectionError, TimeoutError) as e:
                    if isinstance(e, HubError) and not e.retryable:
                        raise
                    last_error = e
                    if attempt < UPLOAD_BLOB_MAX_RETRIES - 1:
                        wait = min(
                            UPLOAD_BLOB_RETRY_BACKOFF ** attempt,
                            UPLOAD_BLOB_RETRY_MAX_WAIT,
                        )
                        logger.warning(
                            "Blob upload attempt %d/%d failed for %s: %s, "
                            "retrying in %ds ...",
                            attempt + 1, UPLOAD_BLOB_MAX_RETRIES,
                            file_path_in_repo, e, wait,
                        )
                        time.sleep(wait)
            else:
                raise StorageError(
                    f"Blob upload failed after {UPLOAD_BLOB_MAX_RETRIES} attempts "
                    f"for {file_path_in_repo}: {last_error}"
                ) from last_error
        else:
            if isinstance(file_path, (str, os.PathLike)):
                current_size = os.path.getsize(str(file_path))
                if current_size != file_size:
                    raise InvalidParameter(
                        f"File size changed since hash computation: "
                        f"was {file_size}, now {current_size}. "
                        f"File may have been modified: {file_path_in_repo}"
                    )
            upload_res = {
                "url": None,
                "is_uploaded": True,
                "is_reused": False,
                "is_blob_uploaded": False,
            }

        return {
            "file_path_in_repo": file_path_in_repo,
            "file_path": file_path,
            "file_mtime": file_stat.st_mtime if file_stat else 0,
            "file_size_on_disk": (
                file_stat.st_size if file_stat
                else hash_info_d.get("file_size", 0)
            ),
            "is_uploaded": upload_res["is_uploaded"],
            "is_reused": upload_res.get("is_reused", False),
            "is_blob_uploaded": upload_res.get("is_blob_uploaded", False),
            "upload_mode": upload_mode,
            "file_hash_info": hash_info_d,
        }

    # ------------------------------------------------------------------
    # Internal: blob upload
    # ------------------------------------------------------------------
    def _upload_blob(
        self,
        *,
        repo_id: str,
        repo_type: str,
        sha256: str,
        size: int,
        data: str | Path | bytes | BinaryIO,
        disable_tqdm: bool = False,
        tqdm_desc: str = "[Uploading]",
        buffer_size_mb: int = 16,
        pre_validated: Any = None,
    ) -> dict:
        res_d: dict = {
            "url": None,
            "is_uploaded": False,
            "is_reused": False,
            "is_blob_uploaded": False,
        }

        if pre_validated is True:
            logger.info("Blob %s already exists globally, reuse.", sha256[:8])
            res_d["is_uploaded"] = True
            res_d["is_reused"] = True
            return res_d

        if isinstance(pre_validated, str):
            upload_url = pre_validated
        else:
            validated = self._client.validate_blobs(
                repo_id=repo_id,
                repo_type=repo_type,
                objects=[{"oid": sha256, "size": size}],
            )
            upload_url = validated.get(sha256)
            if upload_url is None:
                logger.info(
                    "Blob %s already exists globally, reuse.", sha256[:8]
                )
                res_d["is_uploaded"] = True
                res_d["is_reused"] = True
                return res_d

        chunk_size = buffer_size_mb * 1024 * 1024

        with tqdm(
            total=size,
            unit="B",
            unit_scale=True,
            desc=tqdm_desc,
            disable=disable_tqdm,
        ) as pbar:
            if isinstance(data, (str, Path)):
                with open(data, "rb") as f:
                    stream = _CountedReadStream(f, size, pbar, chunk_size)
                    self._client.upload_blob(
                        upload_url=upload_url, data=stream, size=size
                    )
                stream.verify_complete()
            elif isinstance(data, bytes):
                stream = _CountedReadStream(
                    io.BytesIO(data), size, pbar, chunk_size
                )
                self._client.upload_blob(
                    upload_url=upload_url, data=stream, size=size
                )
                stream.verify_complete()
            else:
                stream = _CountedReadStream(data, size, pbar, chunk_size)
                self._client.upload_blob(
                    upload_url=upload_url, data=stream, size=size
                )
                stream.verify_complete()

        res_d["url"] = upload_url
        res_d["is_uploaded"] = True
        res_d["is_blob_uploaded"] = True
        return res_d

    # ------------------------------------------------------------------
    # Internal: batch blob validation
    # ------------------------------------------------------------------
    def _validate_blobs_batch(
        self,
        repo_id: str,
        repo_type: str,
        objects: list[dict],
    ) -> dict[str, str | None]:
        result: dict[str, str | None] = {}
        batch_size = UPLOAD_VALIDATE_BLOB_BATCH_SIZE

        for i in range(0, len(objects), batch_size):
            chunk = objects[i : i + batch_size]
            validated = self._client.validate_blobs(
                repo_id=repo_id,
                repo_type=repo_type,
                objects=chunk,
            )
            result.update(validated)

        return result

    # ------------------------------------------------------------------
    # Internal: commit with retry
    # ------------------------------------------------------------------
    def _commit_with_retry(
        self,
        *,
        repo_id: str,
        repo_type: str,
        operations: list[dict],
        commit_message: str,
        revision: str = "master",
        max_retries: int = UPLOAD_COMMIT_MAX_RETRIES,
    ) -> dict:
        last_error = None
        start_time = time.monotonic()
        for attempt in range(max_retries):
            try:
                return self._client.create_commit(
                    repo_id=repo_id,
                    repo_type=repo_type,
                    operations=operations,
                    commit_message=commit_message,
                    revision=revision,
                )
            except HubError as e:
                if not e.retryable:
                    error_str = str(e)
                    retryable_patterns = ["Could not update refs", "try again"]
                    if not any(p in error_str for p in retryable_patterns):
                        raise
                last_error = e
            except (ConnectionError, TimeoutError) as e:
                last_error = e
            except Exception as e:
                last_error = e

            wait = min(2**attempt, 60)
            elapsed = time.monotonic() - start_time
            if elapsed + wait > UPLOAD_COMMIT_MAX_TOTAL_WAIT:
                logger.error(
                    "Commit total wait time would exceed %ds (already %.1fs elapsed), aborting retries.",
                    UPLOAD_COMMIT_MAX_TOTAL_WAIT,
                    elapsed,
                )
                break
            logger.warning(
                "Commit attempt %d/%d failed: %s, retrying in %ds ...",
                attempt + 1, max_retries, last_error, wait,
            )
            time.sleep(wait)

        if isinstance(last_error, HubError):
            raise last_error
        raise NetworkError(
            f"Commit failed after {max_retries} attempts: {last_error}"
        ) from last_error

    # ------------------------------------------------------------------
    # Internal: build operations
    # ------------------------------------------------------------------
    def _build_operation(
        self,
        path_in_repo: str,
        path_or_fileobj: PathOrFileObj,
        hash_info: dict,
        upload_mode: str,
        is_uploaded: bool,
    ) -> dict:
        if upload_mode == "lfs":
            return {
                "action": "create",
                "path": path_in_repo,
                "type": "lfs",
                "size": hash_info["file_size"],
                "sha256": hash_info["file_hash"],
                "content": "",
                "encoding": "",
            }
        else:
            if isinstance(path_or_fileobj, bytes):
                content_bytes = path_or_fileobj
            elif isinstance(path_or_fileobj, (str, Path)):
                content_bytes = Path(path_or_fileobj).read_bytes()
            else:
                pos = path_or_fileobj.tell()
                content_bytes = path_or_fileobj.read()
                path_or_fileobj.seek(pos)
            return {
                "action": "create",
                "path": path_in_repo,
                "type": "normal",
                "size": hash_info["file_size"],
                "sha256": "",
                "content": base64.b64encode(content_bytes).decode(),
                "encoding": "base64",
            }

    def _build_batch_operations(
        self, results: list[dict], repo_type: str
    ) -> list[dict]:
        operations = []
        for item_d in results:
            file_path = item_d["file_path"]
            hash_info = item_d["file_hash_info"]
            upload_mode = item_d.get("upload_mode") or _upload_mode(
                item_d["file_path_in_repo"],
                hash_info["file_size"],
                repo_type,
            )
            op = self._build_operation(
                path_in_repo=item_d["file_path_in_repo"],
                path_or_fileobj=file_path,
                hash_info=hash_info,
                upload_mode=upload_mode,
                is_uploaded=item_d["is_uploaded"],
            )
            operations.append(op)
        return operations

    # ------------------------------------------------------------------
    # Internal: tracker helpers
    # ------------------------------------------------------------------
    def _track_uploaded_batch(
        self,
        tracker: UploadTracker | NullTracker,
        results: list[dict],
    ) -> None:
        for r in results:
            tracker.mark_uploaded(
                r["file_path_in_repo"], r["file_mtime"], r["file_size_on_disk"]
            )
        tracker.save()

    def _track_committed_batch(
        self,
        tracker: UploadTracker | NullTracker,
        results: list[dict],
    ) -> None:
        tracker.mark_committed_batch(
            [
                (r["file_path_in_repo"], r["file_mtime"], r["file_size_on_disk"])
                for r in results
            ]
        )
        tracker.save()

    # ------------------------------------------------------------------
    # Internal: file collection
    # ------------------------------------------------------------------
    def _prepare_upload_folder(
        self,
        folder_path: str | Path,
        path_in_repo: str,
        repo_type: str = "model",
        allow_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
    ) -> list[tuple[str, str]]:
        folder = Path(folder_path).expanduser().resolve()
        if not folder.is_dir():
            raise InvalidParameter(f"Provided path: '{folder}' is not a directory")

        all_files = sorted(
            path for path in folder.glob("**/*") if path.is_file()
        )

        if len(all_files) > UPLOAD_MAX_FILE_COUNT:
            raise InvalidParameter(
                f"Too many files ({len(all_files)}) in folder, "
                f"max allowed: {UPLOAD_MAX_FILE_COUNT}"
            )

        # Per-directory file count check
        dir_counts: dict[str, int] = {}
        for path in all_files:
            parent = str(path.parent)
            dir_counts[parent] = dir_counts.get(parent, 0) + 1
        for dir_path, count in dir_counts.items():
            if count > UPLOAD_MAX_FILE_COUNT_IN_DIR:
                raise InvalidParameter(
                    f"Too many files ({count}) in directory {dir_path}, "
                    f"max allowed per directory: {UPLOAD_MAX_FILE_COUNT_IN_DIR}"
                )

        # File size checks
        total_size = 0
        normal_size = 0
        for path in all_files:
            fsize = path.stat().st_size
            if fsize > UPLOAD_MAX_FILE_SIZE:
                raise InvalidParameter(
                    f"File too large: {path} ({fsize / 1024 / 1024:.1f} MB), "
                    f"max allowed: {UPLOAD_MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
                )
            total_size += fsize
            if not _is_lfs(str(path), fsize, repo_type):
                normal_size += fsize

        if normal_size > UPLOAD_NORMAL_FILE_SIZE_TOTAL_LIMIT:
            logger.warning(
                "Total normal (non-LFS) file size %d bytes exceeds soft "
                "limit %d bytes. Consider using LFS for large files.",
                normal_size,
                UPLOAD_NORMAL_FILE_SIZE_TOTAL_LIMIT,
            )

        relpath_to_abspath = {
            path.relative_to(folder).as_posix(): str(path)
            for path in all_files
        }

        filtered_keys = _filter_repo_objects(
            list(relpath_to_abspath.keys()),
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
        )

        prefix = f"{path_in_repo.strip('/')}/" if path_in_repo else ""
        prepared = [
            (prefix + relpath, relpath_to_abspath[relpath])
            for relpath in filtered_keys
        ]

        logger.info("Prepared %d files for upload.", len(prepared))
        return prepared

    # ------------------------------------------------------------------
    # Internal: ReAct progressive retry
    # ------------------------------------------------------------------
    def _retry_failed_files_react(
        self,
        failed_files: list[tuple],
        tracker: UploadTracker | NullTracker,
        repo_id: str,
        repo_type: str,
        commit_message: str,
        revision: str,
        max_workers: int,
        disable_tqdm: bool = False,
    ) -> tuple[list[tuple], list[dict], list[dict]]:
        commit_infos: list[dict] = []
        all_successes: list[dict] = []
        retry_counts: dict[str, int] = {}
        permanent_failures: list[tuple] = []
        retryable = list(failed_files)

        remaining = []
        for item_err in retryable:
            (path_in_repo_r, file_path_r), err = item_err
            category = classify_error(err)
            if _ErrorCategory.is_retryable(category):
                remaining.append(item_err)
            else:
                permanent_failures.append(item_err)
                try:
                    st = (
                        os.stat(file_path_r)
                        if isinstance(file_path_r, (str, os.PathLike))
                        else None
                    )
                except OSError:
                    st = None
                tracker.mark_failed(
                    path_in_repo_r,
                    st.st_mtime if st else 0,
                    st.st_size if st else 0,
                    error_type=category,
                )
                logger.error(
                    "[ReAct] Permanent failure: %s (%s: %s)",
                    path_in_repo_r, category, err,
                )
        retryable = remaining

        round_configs = [
            {
                "name": "Round 1 (parallel)",
                "parallel": True,
                "workers": max(1, max_workers // 2),
                "batch_size": 16,
                "delay": 0,
            },
            {
                "name": "Round 2 (serial+backoff)",
                "parallel": False,
                "workers": 1,
                "batch_size": 8,
                "delay": UPLOAD_REACT_ROUND2_BASE_DELAY,
            },
            {
                "name": "Round 3 (single-file)",
                "parallel": False,
                "workers": 1,
                "batch_size": 1,
                "delay": UPLOAD_REACT_ROUND3_FILE_DELAY,
            },
        ]

        for round_idx, cfg in enumerate(round_configs):
            if not retryable:
                break

            round_name = cfg["name"]
            logger.info(
                "[ReAct] %s: retrying %d file(s) ...",
                round_name, len(retryable),
            )

            round_successes: list[dict] = []
            round_failures: list[tuple] = []

            if cfg["parallel"] and len(retryable) > 1:
                with ThreadPoolExecutor(
                    max_workers=cfg["workers"]
                ) as executor:
                    future_map: dict = {}
                    for (path_in_repo_r, file_path_r), _err in retryable:
                        future = executor.submit(
                            self._upload_single_file,
                            path_in_repo_r,
                            file_path_r,
                            repo_id=repo_id,
                            repo_type=repo_type,
                            tracker=tracker,
                            disable_tqdm=disable_tqdm,
                        )
                        future_map[future] = (path_in_repo_r, file_path_r)
                    for future in as_completed(future_map):
                        path_in_repo_r, file_path_r = future_map[future]
                        try:
                            result = future.result()
                            round_successes.append(result)
                        except Exception as e:
                            round_failures.append(
                                ((path_in_repo_r, file_path_r), e)
                            )
            else:
                for i, ((path_in_repo_r, file_path_r), _err) in enumerate(
                    retryable
                ):
                    if cfg["delay"] > 0 and i > 0:
                        delay = (
                            cfg["delay"]
                            * (
                                2
                                ** min(i, UPLOAD_REACT_BACKOFF_MAX_EXPONENT)
                            )
                            if round_idx == 1
                            else cfg["delay"]
                        )
                        delay = min(delay, UPLOAD_REACT_MAX_DELAY)
                        logger.info(
                            "[ReAct] Waiting %ds before retrying %s ...",
                            delay, path_in_repo_r,
                        )
                        time.sleep(delay)
                    try:
                        result = self._upload_single_file(
                            path_in_repo_r,
                            file_path_r,
                            repo_id=repo_id,
                            repo_type=repo_type,
                            tracker=tracker,
                            disable_tqdm=disable_tqdm,
                        )
                        round_successes.append(result)
                    except Exception as e:
                        logger.error(
                            "[ReAct] %s: failed %s - %s",
                            round_name, path_in_repo_r, e,
                        )
                        round_failures.append(
                            ((path_in_repo_r, file_path_r), e)
                        )

            all_successes.extend(round_successes)

            batch_size = min(
                cfg["batch_size"], max(1, len(round_successes))
            )
            for batch_start in range(0, len(round_successes), batch_size):
                batch = round_successes[batch_start : batch_start + batch_size]
                self._track_uploaded_batch(tracker, batch)

                operations = self._build_batch_operations(batch, repo_type)
                if not operations:
                    continue
                try:
                    commit_info = self._commit_with_retry(
                        repo_id=repo_id,
                        repo_type=repo_type,
                        operations=operations,
                        commit_message=f"{commit_message} ({round_name})",
                        revision=revision,
                    )
                    commit_infos.append(commit_info)
                    self._track_committed_batch(tracker, batch)
                    logger.info(
                        "[ReAct] %s: committed %d file(s).",
                        round_name, len(batch),
                    )
                except Exception as e:
                    logger.error(
                        "[ReAct] %s commit failed: %s", round_name, e
                    )
                    category = classify_error(e)
                    if not _ErrorCategory.is_retryable(category):
                        for r in batch:
                            tracker.mark_failed(
                                r["file_path_in_repo"],
                                r["file_mtime"],
                                r["file_size_on_disk"],
                                error_type="commit_" + category,
                            )
                    else:
                        for r in batch:
                            round_failures.append(
                                ((r["file_path_in_repo"], r["file_path"]), e)
                            )

            new_retryable = []
            for item_err in round_failures:
                (path_in_repo_r, file_path_r), err = item_err
                retry_counts[path_in_repo_r] = (
                    retry_counts.get(path_in_repo_r, 0) + 1
                )
                if retry_counts[path_in_repo_r] >= 3:
                    permanent_failures.append(item_err)
                    try:
                        st = (
                            os.stat(file_path_r)
                            if isinstance(file_path_r, (str, os.PathLike))
                            else None
                        )
                    except OSError:
                        st = None
                    tracker.mark_failed(
                        path_in_repo_r,
                        st.st_mtime if st else 0,
                        st.st_size if st else 0,
                        error_type="max_retries_exceeded",
                    )
                    logger.error(
                        "[ReAct] Max retries exceeded for %s", path_in_repo_r
                    )
                    continue
                category = classify_error(err)
                if _ErrorCategory.is_retryable(category):
                    new_retryable.append(item_err)
                else:
                    permanent_failures.append(item_err)
                    try:
                        st = (
                            os.stat(file_path_r)
                            if isinstance(file_path_r, (str, os.PathLike))
                            else None
                        )
                    except OSError:
                        st = None
                    tracker.mark_failed(
                        path_in_repo_r,
                        st.st_mtime if st else 0,
                        st.st_size if st else 0,
                        error_type=category,
                    )
                    logger.error(
                        "[ReAct] Permanent failure: %s (%s)",
                        path_in_repo_r, category,
                    )

            progress = len(retryable) - len(new_retryable)
            if progress > 0:
                logger.info(
                    "[ReAct] %s: made progress — %d file(s) resolved, "
                    "%d remaining.",
                    round_name, progress, len(new_retryable),
                )
            elif new_retryable:
                logger.warning(
                    "[ReAct] %s: no progress, escalating to next round.",
                    round_name,
                )

            retryable = new_retryable

        all_failures = permanent_failures + retryable
        if retryable:
            logger.error(
                "[ReAct] %d file(s) still failing after all retry rounds.",
                len(retryable),
            )

        return all_failures, commit_infos, all_successes

    # ------------------------------------------------------------------
    # Internal: simple retry (when ReAct is disabled)
    # ------------------------------------------------------------------
    def _retry_failed_simple(
        self,
        failed_files: list[tuple],
        tracker: UploadTracker | NullTracker,
        repo_id: str,
        repo_type: str,
        commit_message: str,
        commit_description: str | None,
        revision: str,
        commit_infos: list[dict],
        all_results: list[dict],
        disable_tqdm: bool = False,
    ) -> list[tuple]:
        total_failed_files = list(failed_files)
        for retry_round in range(UPLOAD_FAILED_FILE_MAX_RETRIES):
            if not total_failed_files:
                break
            logger.info(
                "Retry round %d/%d: re-uploading %d failed file(s) ...",
                retry_round + 1, UPLOAD_FAILED_FILE_MAX_RETRIES,
                len(total_failed_files),
            )
            retry_failures: list[tuple] = []
            retry_successes: list[dict] = []
            for (path_in_repo_r, file_path_r), _err in total_failed_files:
                try:
                    result = self._upload_single_file(
                        path_in_repo_r,
                        file_path_r,
                        repo_id=repo_id,
                        repo_type=repo_type,
                        tracker=tracker,
                        disable_tqdm=disable_tqdm,
                    )
                    retry_successes.append(result)
                except Exception as e:
                    logger.error("  Retry failed: %s - %s", path_in_repo_r, e)
                    retry_failures.append(
                        ((path_in_repo_r, file_path_r), e)
                    )
            if retry_successes:
                self._track_uploaded_batch(tracker, retry_successes)
                operations = self._build_batch_operations(
                    retry_successes, repo_type
                )
                if operations:
                    try:
                        commit_info = self._commit_with_retry(
                            repo_id=repo_id,
                            repo_type=repo_type,
                            operations=operations,
                            commit_message=(
                                f"{commit_message} "
                                f"(retry round {retry_round + 1})"
                            ),
                            revision=revision,
                        )
                        commit_infos.append(commit_info)
                        all_results.extend(retry_successes)
                        self._track_committed_batch(
                            tracker, retry_successes
                        )
                        logger.info(
                            "  Retry round %d: committed %d file(s).",
                            retry_round + 1, len(retry_successes),
                        )
                    except Exception as e:
                        logger.error(
                            "  Retry round %d commit failed: %s",
                            retry_round + 1, e,
                        )
                        category = classify_error(e)
                        if not _ErrorCategory.is_retryable(category):
                            for result in retry_successes:
                                tracker.mark_failed(
                                    result["file_path_in_repo"],
                                    result["file_mtime"],
                                    result["file_size_on_disk"],
                                    error_type="commit_" + category,
                                )
                        else:
                            for result in retry_successes:
                                retry_failures.append(
                                    (
                                        (
                                            result["file_path_in_repo"],
                                            result.get("file_path", ""),
                                        ),
                                        e,
                                    )
                                )
            total_failed_files = retry_failures
        return total_failed_files
