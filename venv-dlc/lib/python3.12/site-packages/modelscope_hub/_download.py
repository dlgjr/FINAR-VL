"""Internal file download implementation.

Supports single-file and whole-repo (snapshot) downloads with:
- HTTP Range-based resume
- SHA256 integrity verification
- tqdm progress display
- Parallel downloads via ThreadPoolExecutor
- Parallel range download (split large files into parts)
- Per-file download retry with backoff
- File lock for multiprocess safety
- User-agent / snapshot headers
- Intra-cloud acceleration
- Local-files-only (offline) mode
- Custom progress callbacks
- Local snapshot cache directory management
"""

from __future__ import annotations

import contextlib
import copy
import errno
import fnmatch
import hashlib
import io
import os
import time
import re
import threading

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
from tqdm.auto import tqdm
from urllib3.util.retry import Retry

from .constants import (
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_PARALLEL_THRESHOLD,
    DOWNLOAD_PARALLELS,
    DOWNLOAD_PART_SIZE,
    DOWNLOAD_RETRY_TIMES,
    DOWNLOAD_TIMEOUT,
    ENV_FILE_LOCK,
    ENV_INTRA_CLOUD_ACCELERATION,
    ENV_INTRA_CLOUD_REGION,
    ENV_INTER_CLOUD_REGIONS,
)
from .errors import (
    CacheNotFound,
    FileIntegrityError,
    NetworkError,
    NotExistError,
    PermissionDeniedError,
    RequestTimeoutError,
)
from .utils.file_utils import compute_hash, ensure_dir
from .utils.logger import get_logger

if TYPE_CHECKING:
    from .config import HubConfig
    from ._legacy_api import LegacyClient

logger = get_logger("download")

DOWNLOAD_HASH_RETRY_TIMES = 3


# ---------------------------------------------------------------------------
# Progress callback system
# ---------------------------------------------------------------------------
class ProgressCallback:
    """Base class for download progress callbacks.

    Subclass and override :meth:`update` / :meth:`end` to track download
    progress. Instances are created per-file by
    ``callback_cls(filename, file_size)``.
    """

    def __init__(self, filename: str, file_size: int):
        self.filename = filename
        self.file_size = file_size

    def update(self, size: int) -> None:
        pass

    def end(self) -> None:
        pass


class TqdmCallback(ProgressCallback):
    """Progress callback backed by tqdm."""

    def __init__(self, filename: str, file_size: int):
        super().__init__(filename, file_size)
        self.progress = tqdm(
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            total=file_size if file_size > 0 else 1,
            initial=0,
            desc=f"Downloading [{self.filename}]",
            leave=True,
        )

    def update(self, size: int) -> None:
        self.progress.update(size)

    def end(self) -> None:
        self.progress.close()


# ---------------------------------------------------------------------------
# File lock
# ---------------------------------------------------------------------------
_STALE_LOCK_SECONDS = 2 * 3600


@contextlib.contextmanager
def _optional_file_lock(lock_path: Path | None, *, enabled: bool = True):
    """Acquire a file lock when *enabled*, otherwise no-op."""
    if not enabled or lock_path is None:
        yield
        return

    from filelock import FileLock, SoftFileLock, Timeout

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    default_interval = 60
    lock = FileLock(str(lock_path), timeout=default_interval)
    is_soft = False
    waited = 0

    while True:
        try:
            lock.acquire(timeout=default_interval)
        except Timeout:
            waited += default_interval
            if is_soft and waited >= _STALE_LOCK_SECONDS:
                try:
                    age = time.time() - lock_path.stat().st_mtime
                except OSError:
                    age = 0
                if age >= _STALE_LOCK_SECONDS:
                    logger.warning(
                        "Removing possibly stale SoftFileLock (age=%.0fs): %s",
                        age, lock_path,
                    )
                    try:
                        lock_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                    waited = 0
                    continue
            logger.info(
                "Still waiting to acquire lock on %s",
                lock_path,
            )
        except NotImplementedError as exc:
            if "use SoftFileLock instead" in str(exc):
                logger.warning(
                    "Filesystem does not support flock, falling back to SoftFileLock for %s",
                    lock_path,
                )
                lock = SoftFileLock(str(lock_path), timeout=default_interval)
                is_soft = True
                continue
            raise
        except OSError as exc:
            if exc.errno in (errno.ESTALE, errno.ENOENT, getattr(errno, "EREMOTEIO", -1)):
                logger.warning(
                    "OSError (errno=%d) on %s, falling back to SoftFileLock.",
                    exc.errno, lock_path,
                )
                lock = SoftFileLock(str(lock_path), timeout=default_interval)
                is_soft = True
                continue
            raise
        else:
            break

    try:
        yield lock
    finally:
        try:
            lock.release()
        except OSError:
            try:
                lock_path.unlink()
            except OSError:
                pass


def _file_lock_enabled() -> bool:
    """Check whether file locking is enabled via environment."""
    from .constants import _env_bool
    return _env_bool(ENV_FILE_LOCK, True)


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------
def _matches_patterns(path: str, patterns: list[str] | None) -> bool:
    """Check if path matches any of the glob patterns.

    Also accepts legacy regex-style patterns (e.g. ``.*\\.bin``) by
    converting ``.*`` to ``*`` before matching.
    """
    if not patterns:
        return False
    for pat in patterns:
        if fnmatch.fnmatch(path, pat):
            return True
        if ".*" in pat:
            glob_pat = pat.replace(".*", "*")
            if fnmatch.fnmatch(path, glob_pat):
                return True
    return False


# ---------------------------------------------------------------------------
# Parallel range download
# ---------------------------------------------------------------------------
def _download_part_with_retry(params: tuple) -> None:
    """Download a byte range with retry and resume support."""
    file_path, progress_callbacks, start, end, url, file_name, headers, cookies = params
    get_headers = {} if headers is None else copy.deepcopy(headers)
    get_headers["X-Request-ID"] = uuid.uuid4().hex
    retry = Retry(
        total=DOWNLOAD_RETRY_TIMES,
        backoff_factor=1,
        allowed_methods=["GET"],
    )
    part_file_name = f"{file_path}_{start}_{end}"
    while True:
        try:
            partial_length = 0
            if os.path.exists(part_file_name):
                with open(part_file_name, "rb") as f:
                    partial_length = f.seek(0, io.SEEK_END)
                    for cb in progress_callbacks:
                        cb.update(partial_length)
            download_start = start + partial_length
            if download_start > end:
                break
            get_headers["Range"] = f"bytes={download_start}-{end}"
            with open(part_file_name, "ab+") as f:
                r = requests.get(
                    url, stream=True, headers=get_headers,
                    cookies=cookies, timeout=DOWNLOAD_TIMEOUT,
                )
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        for cb in progress_callbacks:
                            cb.update(len(chunk))
            break
        except Exception as exc:
            retry = retry.increment("GET", url, error=exc)
            logger.warning("Downloading part %s-%s failed: %s, will retry", start, end, exc)
            retry.sleep()


def _parallel_download(
    url: str,
    target: Path,
    file_size: int,
    headers: dict[str, str] | None,
    cookies: dict | None,
    progress_callbacks: list[ProgressCallback] | None = None,
) -> str:
    """Split a large file into parts and download in parallel.

    Returns the SHA256 hex digest of the merged file.
    """
    callbacks = progress_callbacks or []
    part_size = DOWNLOAD_PART_SIZE
    tasks: list[tuple] = []
    file_path = str(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    num_full_parts = file_size // part_size
    for idx in range(num_full_parts):
        start = idx * part_size
        end = (idx + 1) * part_size - 1
        tasks.append((file_path, callbacks, start, end, url, target.name, headers, cookies))
    remainder_start = num_full_parts * part_size
    if remainder_start < file_size:
        tasks.append((file_path, callbacks, remainder_start, file_size - 1, url, target.name, headers, cookies))

    parallels = min(DOWNLOAD_PARALLELS, 16)
    with ThreadPoolExecutor(max_workers=parallels, thread_name_prefix="download") as executor:
        list(executor.map(_download_part_with_retry, tasks))

    for cb in callbacks:
        cb.end()

    hash_sha256 = hashlib.sha256()
    tmp_target = target.with_suffix(target.suffix + ".parallel_tmp")
    with open(tmp_target, "wb") as output_file:
        for task in tasks:
            part_file_name = f"{task[0]}_{task[2]}_{task[3]}"
            with open(part_file_name, "rb") as part_file:
                while True:
                    chunk = part_file.read(16 * DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    output_file.write(chunk)
                    hash_sha256.update(chunk)
            os.remove(part_file_name)
    tmp_target.replace(target)
    return hash_sha256.hexdigest()


# ---------------------------------------------------------------------------
# Download manager
# ---------------------------------------------------------------------------
class DownloadManager:
    """Internal file download implementation.

    Dependencies are injected via constructor to keep this class testable.
    """

    def __init__(self, legacy_client: "LegacyClient", config: "HubConfig") -> None:
        self._client = legacy_client
        self._config = config
        self._cached_region: str | None = None
        # Cache resolved inter-region probe results to avoid redundant HEAD probes
        # when downloading multiple files from the same repo in parallel.
        self._inter_region_cache: dict[tuple[str, str], tuple[str | None, str]] = {}
        self._inter_region_lock = threading.Lock()

    # ------------------------------------------------------------------
    # User-agent & headers
    # ------------------------------------------------------------------
    def _build_user_agent(self, user_agent: dict | str | None = None) -> str:
        from .utils import build_user_agent

        return build_user_agent(
            session_id=self._config.get_session_id(),
            extra=user_agent,
        )

    def _detect_region(self) -> str:
        """Detect Alibaba cloud region ID for intra-cloud acceleration."""
        if self._cached_region is not None:
            return self._cached_region

        endpoint = self._client.endpoint
        internal_url = f"{endpoint}/api/v1/repos/internalAccelerationInfo"

        def _get(url: str, timeout: float):
            try:
                resp = requests.get(url, timeout=timeout)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException:
                return None

        region_id = ""
        resp = _get(internal_url, 0.2)
        if resp is not None:
            data = resp.json()
            query_addr = ""
            if "Data" in data:
                query_addr = data["Data"].get("InternalRegionQueryAddress", "")
            if query_addr:
                domain_resp = _get(query_addr, 0.2)
                if domain_resp is not None:
                    region_id = domain_resp.text.strip()

        self._cached_region = region_id
        return region_id

    # OSS internal endpoint hostname pattern:
    #   <prefix>.oss<region>-internal.aliyuncs.com
    # e.g. modelhub-cn-hangzhou.oss-cn-hangzhou-internal.aliyuncs.com
    _OSS_INTERNAL_RE = re.compile(
        r".*\.oss.*-internal\.aliyuncs\.com$"
    )

    @staticmethod
    def _is_oss_internal_url(url: str) -> bool:
        """Check if a URL points to an OSS internal (intranet) endpoint.

        Matches hostnames like:
            modelhub-cn-hangzhou.oss-cn-hangzhou-internal.aliyuncs.com
        """
        try:
            host = urlparse(url).hostname or ""
        except Exception:
            return False
        return bool(DownloadManager._OSS_INTERNAL_RE.match(host))

    @staticmethod
    def _probe_redirect_url(
        url: str,
        headers: dict[str, str],
        cookies: dict | None = None,
        timeout: float = 5.0,
    ) -> str:
        """Send a HEAD request without following redirects to get the 302 Location."""
        try:
            r = requests.head(
                url, headers=headers, cookies=cookies,
                allow_redirects=False, timeout=timeout,
            )
            if r.status_code in (301, 302, 303, 307, 308):
                return r.headers.get("Location", "")
        except requests.exceptions.RequestException:
            pass
        return ""

    def _get_inter_cloud_regions(self) -> list[str]:
        """Read the inter-cloud peer region list from the environment."""
        from .constants import _env
        raw = _env(ENV_INTER_CLOUD_REGIONS, "INTER_CLOUD_ACCELERATION_REGIONS") or ""
        return [r.strip().lower() for r in raw.split(",") if r.strip()]

    def _resolve_inter_region_headers(
        self,
        url: str,
        headers: dict[str, str],
        cookies: dict | None = None,
        peer_regions: list[str] | None = None,
    ) -> tuple[dict[str, str], str]:
        """Probe peer regions and return headers with the best region for OSS internal download.

        Steps:
        1. Probe with current (local) region — if already OSS internal, return as-is.
        2. Try each peer region in order (skip duplicates of local) — first OSS internal hit wins.
        3. If all miss, fall back to original headers (default path).

        Returns:
            (headers, source) where source is "local", "peer", or "default".
        """
        if peer_regions is None:
            peer_regions = self._get_inter_cloud_regions()
        if not peer_regions:
            return headers, "default"

        current_region = headers.get("x-aliyun-region-id", "").lower()

        # Step 1: Probe with current (local) region
        redirect_url = self._probe_redirect_url(url, headers, cookies)
        if self._is_oss_internal_url(redirect_url):
            logger.debug("Inter-region: local region already yields OSS internal URL, skipping.")
            return headers, "local"

        # Step 2: Try each peer region in order
        for peer_region in peer_regions:
            if peer_region == current_region:
                continue
            probe_headers = {**headers, "x-aliyun-region-id": peer_region}
            redirect_url = self._probe_redirect_url(url, probe_headers, cookies)
            if self._is_oss_internal_url(redirect_url):
                logger.debug(
                    'Inter-region acceleration: using peer region "%s" (OSS internal).',
                    peer_region,
                )
                return probe_headers, "peer"

        # Step 3: All peers missed
        logger.debug("Inter-region: no peer region yields OSS internal URL, using default path.")
        return headers, "default"

    def _build_download_headers(
        self,
        user_agent: dict | str | None = None,
    ) -> dict[str, str]:
        from .constants import _env, _env_bool

        headers: dict[str, str] = {
            "user-agent": self._build_user_agent(user_agent),
            "snapshot-identifier": uuid.uuid4().hex,
        }
        if _env_bool(ENV_INTRA_CLOUD_ACCELERATION, True):
            region = (_env(ENV_INTRA_CLOUD_REGION, "INTRA_CLOUD_ACCELERATION_REGION") or "").strip()
            if not region:
                try:
                    region = self._detect_region()
                except Exception:
                    region = ""
            if region:
                headers["x-aliyun-region-id"] = region
        return headers

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def download_file(
        self,
        repo_id: str,
        repo_type: str,
        file_path: str,
        revision: str = "master",
        cache_dir: Path | None = None,
        local_dir: Path | None = None,
        force: bool = False,
        expected_sha256: str | None = None,
        local_files_only: bool = False,
        file_size: int | None = None,
        user_agent: dict | str | None = None,
        progress_callbacks: list[type[ProgressCallback]] | None = None,
    ) -> Path:
        """Download a single file from a repository.

        When *local_dir* is provided the file is placed directly under that
        directory (preserving relative path structure).  Otherwise the
        standard cache layout is used::

            {cache_dir}/{type}s/{owner}--{name}/snapshots/{revision}/{file_path}

        Parameters
        ----------
        repo_id:
            Repository identifier (``owner/name``).
        repo_type:
            One of the :class:`~.constants.RepoType` values.
        file_path:
            Path within the repository.
        revision:
            Branch, tag, or commit hash.
        cache_dir:
            Override for the default cache directory.
        local_dir:
            When set, download directly into this directory instead of cache.
        force:
            Re-download even if file exists in cache.
        expected_sha256:
            When provided, verify downloaded file hash and use it for
            cache hit validation.
        local_files_only:
            When ``True``, return the cached path without network access.
            Raises ``ValueError`` if the file is not cached.
        file_size:
            Known file size (enables parallel range download for large files).
        user_agent:
            Custom user-agent info appended to the default UA string.
        progress_callbacks:
            List of :class:`ProgressCallback` *classes* (not instances).
            Each class is instantiated per-file with ``(filename, file_size)``.

        Returns
        -------
        Path
            Absolute path to the downloaded (or cached) file on disk.
        """
        if local_dir is not None:
            target = Path(local_dir) / file_path
        else:
            # Fallback: reuse old SDK (<=1.37) cache if it exists
            legacy = self._find_legacy_repo_dir(repo_id, repo_type, cache_dir)
            if legacy is not None:
                target = legacy / file_path
            else:
                root = self._repo_cache_dir(repo_id, repo_type, cache_dir)
                target = root / "snapshots" / revision / file_path

        if local_files_only:
            if target.exists():
                return target
            raise CacheNotFound(
                "Cannot find the requested files in the cached path and outgoing"
                " traffic has been disabled. To enable look-ups and downloads"
                " online, set 'local_files_only' to False.",
                cache_dir=str(target.parent),
            )

        if not force and self._cache_hit(target, expected_sha256):
            return target

        use_lock = _file_lock_enabled()
        lock_path = self._lock_path(repo_id, repo_type, cache_dir=cache_dir, file_path=file_path) if use_lock else None
        with _optional_file_lock(lock_path, enabled=use_lock):
            # Re-check after acquiring lock — another process may have finished.
            if not force and self._cache_hit(target, expected_sha256):
                return target

            ensure_dir(target.parent)

            for attempt in range(DOWNLOAD_HASH_RETRY_TIMES):
                self._download_with_resume(
                    repo_id, repo_type, file_path, revision, target,
                    file_size=file_size,
                    user_agent=user_agent,
                    progress_callbacks=progress_callbacks,
                )

                if not expected_sha256:
                    break

                try:
                    self.verify_file(target, expected_sha256)
                    break
                except FileIntegrityError:
                    if attempt < DOWNLOAD_HASH_RETRY_TIMES - 1:
                        logger.warning(
                            "Hash validation failed for %s, retrying (%d/%d)",
                            file_path, attempt + 1, DOWNLOAD_HASH_RETRY_TIMES,
                        )
                        target.unlink(missing_ok=True)
                    else:
                        raise

        return target

    def download_repo(
        self,
        repo_id: str,
        repo_type: str,
        revision: str = "master",
        cache_dir: Path | None = None,
        local_dir: Path | None = None,
        allow_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        max_workers: int = 4,
        local_files_only: bool = False,
        user_agent: dict | str | None = None,
        progress_callbacks: list[type[ProgressCallback]] | None = None,
    ) -> Path:
        """Download an entire repository (snapshot download).

        Parameters
        ----------
        repo_id:
            Repository identifier (``owner/name``).
        repo_type:
            One of the :class:`~.constants.RepoType` values.
        revision:
            Branch, tag, or commit hash.
        cache_dir:
            Override for the default cache directory.
        local_dir:
            When set, download directly into this directory instead of cache.
        allow_patterns:
            Only files matching these globs will be downloaded.
        ignore_patterns:
            Files matching these globs will be skipped.
        max_workers:
            Number of parallel download threads.
        local_files_only:
            When ``True``, return the cached snapshot path without network.
        user_agent:
            Custom user-agent info for download headers.
        progress_callbacks:
            List of :class:`ProgressCallback` *classes* (not instances).

        Returns
        -------
        Path
            Absolute path to the snapshot/local directory.
        """
        if local_dir is not None:
            output_dir = ensure_dir(Path(local_dir))
        else:
            # Fallback: reuse old SDK (<=1.37) cache if it exists
            legacy = self._find_legacy_repo_dir(repo_id, repo_type, cache_dir)
            if legacy is not None:
                logger.info(
                    "Found legacy cache at %s, reusing.", legacy,
                )
                output_dir = legacy
                local_dir = legacy
            else:
                root = self._repo_cache_dir(repo_id, repo_type, cache_dir)
                output_dir = ensure_dir(root / "snapshots" / revision)

        if local_files_only:
            if any(output_dir.iterdir()):
                logger.warning(
                    "Cannot confirm the cached file is for revision: %s", revision
                )
                return output_dir
            raise CacheNotFound(
                "Cannot find the requested files in the cached path and outgoing"
                " traffic has been disabled. To enable look-ups and downloads"
                " online, set 'local_files_only' to False.",
                cache_dir=str(output_dir),
            )

        if repo_type in ("skill", "skills"):
            return self._download_archive(
                repo_id=repo_id,
                repo_type=repo_type,
                revision=revision,
                output_dir=output_dir,
            )

        if repo_type in ("dataset", "datasets"):
            files = self._client.list_dataset_files_paginated(
                repo_id=repo_id,
                revision=revision,
            )
        else:
            files = self._client.list_repo_files(
                repo_id=repo_id,
                repo_type=repo_type,
                revision=revision,
                recursive=True,
            )

        download_items: list[tuple[str, str | None, int | None]] = []
        for f in files:
            path = f.get("Path") or f.get("path") or f.get("Name") or ""
            ftype = f.get("Type") or f.get("type") or "blob"
            if ftype == "tree":
                continue
            if not path:
                continue
            if allow_patterns and not _matches_patterns(path, allow_patterns):
                continue
            if ignore_patterns and _matches_patterns(path, ignore_patterns):
                continue
            sha256 = f.get("Sha256") or f.get("sha256") or None
            raw_size = f.get("Size") or f.get("size")
            size = int(raw_size) if raw_size else None
            download_items.append((path, sha256, size))

        if not download_items:
            logger.info("No files to download for %s@%s", repo_id, revision)
            return output_dir

        logger.info("Downloading %d files from %s@%s", len(download_items), repo_id, revision)

        errors: list[str] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.download_file,
                    repo_id=repo_id,
                    repo_type=repo_type,
                    file_path=fp,
                    revision=revision,
                    cache_dir=cache_dir,
                    local_dir=local_dir,
                    expected_sha256=sha256,
                    file_size=size,
                    user_agent=user_agent,
                    progress_callbacks=progress_callbacks,
                ): fp
                for fp, sha256, size in download_items
            }

            with tqdm(total=len(download_items), desc="Downloading", unit="file") as pbar:
                for future in as_completed(futures):
                    fp = futures[future]
                    try:
                        future.result()
                    except Exception as exc:
                        errors.append(f"{fp}: {exc}")
                        logger.error("Failed to download %s: %s", fp, exc)
                    finally:
                        pbar.update(1)

        if errors:
            logger.warning("%d file(s) failed to download", len(errors))

        return output_dir

    # ------------------------------------------------------------------
    # Internal: archive-based download (skills)
    # ------------------------------------------------------------------
    def _download_archive(
        self,
        repo_id: str,
        repo_type: str,
        revision: str,
        output_dir: Path,
    ) -> Path:
        """Download a repo via its zip archive endpoint and extract.

        Skill repos do not support per-file ``/repo?FilePath=...`` download.
        The old SDK uses ``/archive/zip/{revision}`` for these.
        """
        import shutil
        import tempfile
        import zipfile

        tmp_path: Path | None = None
        try:
            resp = self._client.download_archive(
                repo_id=repo_id,
                repo_type=repo_type,
                revision=revision,
            )

            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_path = Path(tmp.name)
                for chunk in resp.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if chunk:
                        tmp.write(chunk)

            with zipfile.ZipFile(tmp_path, "r") as zf:
                zf.extractall(output_dir)

            # Flatten if zip has a single top-level directory
            entries = [e for e in output_dir.iterdir()]
            if len(entries) == 1 and entries[0].is_dir():
                nested = entries[0]
                for item in nested.iterdir():
                    shutil.move(str(item), str(output_dir / item.name))
                nested.rmdir()
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

        logger.info("Extracted archive for %s to %s", repo_id, output_dir)
        return output_dir

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _cache_hit(target: Path, expected_sha256: str | None) -> bool:
        """Return True if *target* exists and passes optional hash check."""
        if not target.exists():
            return False
        if expected_sha256:
            actual = compute_hash(target, "sha256")
            if actual != expected_sha256:
                logger.debug("Cache stale (hash mismatch): %s", target)
                return False
            logger.debug("Cache hit (hash verified): %s", target)
        else:
            logger.debug("Cache hit: %s", target)
        return True

    def _repo_cache_dir(
        self,
        repo_id: str,
        repo_type: str,
        cache_dir: Path | None = None,
    ) -> Path:
        """Compute the cache directory for a given repo."""
        base = cache_dir or self._config.cache_dir
        segment = f"{repo_type}s" if not repo_type.endswith("s") else repo_type
        safe_id = repo_id.replace("/", "--")
        return ensure_dir(base / segment / safe_id)

    def _find_legacy_repo_dir(
        self,
        repo_id: str,
        repo_type: str,
        cache_dir: Path | None = None,
    ) -> Path | None:
        """Check for old SDK (<=1.37) cache layout and return it if non-empty.

        Old SDKs encoded dots in the repo name as ``___`` and, when no
        ``MODELSCOPE_CACHE`` was set, stored everything under a ``hub/``
        sub-directory of the cache root. Both historical layouts are probed,
        in priority order::

            {base}/{type}s/{owner}/{name___}        # MODELSCOPE_CACHE explicitly set
            {base}/hub/{type}s/{owner}/{name___}    # default cache (~/.cache/modelscope/hub)

        e.g.  ~/.cache/modelscope/hub/models/Qwen/Qwen3___5-0___8B/

        Returns the first existing, non-empty candidate, or ``None`` when the
        cache is clean (so the caller falls back to the new layout).
        """
        base = cache_dir or self._config.cache_dir
        segment = f"{repo_type}s" if not repo_type.endswith("s") else repo_type
        parts = repo_id.split("/", 1)
        if len(parts) != 2:
            return None
        owner, name = parts
        safe_name = name.replace(".", "___")
        candidates = (
            base / segment / owner / safe_name,
            base / "hub" / segment / owner / safe_name,
        )
        for legacy_path in candidates:
            if not legacy_path.is_dir():
                continue
            try:
                if any(legacy_path.iterdir()):
                    return legacy_path
            except OSError:
                continue
        return None

    def _lock_path(
        self,
        repo_id: str,
        repo_type: str,
        cache_dir: Path | None = None,
        file_path: str | None = None,
    ) -> Path:
        """Compute the lock file path for a given repo or file."""
        base = cache_dir or self._config.cache_dir
        safe_id = repo_id.replace("/", "___")
        if file_path is not None:
            safe_file = file_path.replace("/", "___").replace(".", "_")
            return base / ".lock" / f"{repo_type}_{safe_id}_{safe_file}.lock"
        return base / ".lock" / f"{repo_type}_{safe_id}.lock"

    def _download_with_resume(
        self,
        repo_id: str,
        repo_type: str,
        file_path: str,
        revision: str,
        target: Path,
        *,
        file_size: int | None = None,
        user_agent: dict | str | None = None,
        progress_callbacks: list[type[ProgressCallback]] | None = None,
    ) -> Path:
        """Download a file with HTTP Range resume support and retry."""
        use_parallel = (
            file_size is not None
            and file_size > DOWNLOAD_PARALLEL_THRESHOLD
            and DOWNLOAD_PARALLELS > 1
        )

        download_headers = self._build_download_headers(user_agent)

        # Inter-region acceleration: probe peer regions for OSS internal URL.
        # Cache per (repo_id, repo_type) — all files in the same repo share one
        # OSS bucket so one probe is sufficient for the entire download session.
        # Progress bar prefix: "⚡ " = local OSS, "⇄ " = peer OSS, "  " = CDN, "" = not configured
        source_prefix = ""
        peer_regions = self._get_inter_cloud_regions()
        if peer_regions:
            cache_key = (repo_id, repo_type)
            with self._inter_region_lock:
                cached = self._inter_region_cache.get(cache_key)
                if cached is None:
                    # First thread for this repo — do the probe under lock so
                    # other threads wait instead of issuing redundant HEAD reqs.
                    try:
                        probe_url = self._client.get_download_url(
                            repo_id, repo_type, file_path, revision,
                        )
                        cookies = None
                        if self._client.token:
                            cookies = {"m_session_id": self._client.token}
                        download_headers, source = self._resolve_inter_region_headers(
                            probe_url, download_headers, cookies,
                            peer_regions=peer_regions,
                        )
                        resolved_region = download_headers.get("x-aliyun-region-id")
                        self._inter_region_cache[cache_key] = (resolved_region, source)
                    except Exception as exc:
                        logger.warning(
                            "Failed to resolve inter-region acceleration: %s. Falling back to default.", exc,
                        )
                        self._inter_region_cache[cache_key] = (None, "default")
                        cached = (None, "default")

            if cached is None:
                cached = self._inter_region_cache.get(cache_key)

            if cached is not None:
                resolved_region, source = cached
                if resolved_region is not None:
                    download_headers["x-aliyun-region-id"] = resolved_region
                source_prefix = {
                    "local": "\u26a1 ", "peer": "\u21c4 ", "default": "  ",
                }[source]

        if use_parallel:
            url = self._client.get_download_url(
                repo_id, repo_type, file_path, revision,
            )
            cookies = None
            if self._client.token:
                cookies = {"m_session_id": self._client.token}

            cb_instances = []
            if progress_callbacks:
                cb_instances = [cls(file_path, file_size) for cls in progress_callbacks]

            _parallel_download(
                url=url,
                target=target,
                file_size=file_size,
                headers=download_headers,
                cookies=cookies,
                progress_callbacks=cb_instances,
            )
            return target

        # Single-stream download with retry
        cb_classes = list(progress_callbacks or [])
        cb_instances = [cls(file_path, file_size or 0) for cls in cb_classes]

        retry = Retry(
            total=DOWNLOAD_RETRY_TIMES,
            backoff_factor=1,
            allowed_methods=["GET"],
        )
        tmp_path = target.with_suffix(target.suffix + ".incomplete")

        while True:
            try:
                existing_size = 0
                if tmp_path.exists():
                    existing_size = tmp_path.stat().st_size
                    for cb in cb_instances:
                        cb.update(existing_size)

                extra_headers: dict[str, str] = copy.deepcopy(download_headers)
                extra_headers["X-Request-ID"] = uuid.uuid4().hex
                if existing_size > 0:
                    extra_headers["Range"] = f"bytes={existing_size}-"
                    logger.debug("Resuming download from byte %d", existing_size)

                try:
                    resp = self._client.download_stream(
                        repo_id=repo_id,
                        repo_type=repo_type,
                        file_path=file_path,
                        revision=revision,
                        headers=extra_headers,
                    )
                except requests.Timeout as exc:
                    raise RequestTimeoutError(f"Download timed out for {file_path}: {exc}") from exc
                except requests.ConnectionError as exc:
                    raise NetworkError(f"Download connection failed for {file_path}: {exc}") from exc
                except requests.RequestException as exc:
                    raise NetworkError(f"Download failed for {file_path}: {exc}") from exc

                content_length = resp.headers.get("Content-Length")
                total_size = int(content_length) if content_length else None
                is_resumed = resp.status_code == 206

                if is_resumed and total_size:
                    total_size += existing_size

                mode = "ab" if is_resumed else "wb"
                if not is_resumed:
                    existing_size = 0

                with tqdm(
                    total=total_size,
                    initial=existing_size,
                    unit="B",
                    unit_scale=True,
                    desc=f"{source_prefix}{Path(file_path).name}",
                    leave=False,
                ) as pbar:
                    with open(tmp_path, mode) as fh:
                        for chunk in resp.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                            if chunk:
                                fh.write(chunk)
                                pbar.update(len(chunk))
                                for cb in cb_instances:
                                    cb.update(len(chunk))

                tmp_path.replace(target)
                for cb in cb_instances:
                    cb.end()
                logger.debug("Downloaded: %s", target)
                return target

            except (NotExistError, PermissionDeniedError):
                raise
            except Exception as exc:
                retry = retry.increment("GET", file_path, error=exc)
                logger.warning("Download failed for %s: %s, will retry", file_path, exc)
                retry.sleep()

    def verify_file(self, file_path: Path, expected_sha256: str) -> bool:
        """Verify a downloaded file's SHA256 hash.

        Raises :class:`~.errors.FileIntegrityError` on mismatch.
        """
        actual = compute_hash(file_path, "sha256")
        if actual != expected_sha256:
            raise FileIntegrityError(
                f"Hash mismatch for {file_path.name}: "
                f"expected {expected_sha256[:16]}..., got {actual[:16]}..."
            )
        return True
