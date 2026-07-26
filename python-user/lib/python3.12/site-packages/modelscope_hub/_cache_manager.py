"""Cache management utilities.

Provides scanning and cleanup of the local blob/snapshot cache produced
by :class:`~._download.DownloadManager`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .config import get_default_config
from .constants import RepoType
from .errors import CacheError
from .types import CachedRepoInfo, CacheInfo, CacheVerification, VerificationMismatch
from .utils.file_utils import compute_hash
from .utils.logger import get_logger

logger = get_logger("cache")

# Repo types to scan by default
_DEFAULT_SCAN_TYPES = [RepoType.MODEL, RepoType.DATASET, RepoType.STUDIO, RepoType.MCP]


def scan_cache(cache_dir: Path | None = None) -> CacheInfo:
    """Scan the local cache and return metadata about cached repositories.

    Parameters
    ----------
    cache_dir:
        Override for the cache directory. Defaults to the SDK config default.

    Returns
    -------
    CacheInfo
        Summary of all cached repositories, total size, etc.
    """
    config = get_default_config()
    root = Path(cache_dir) if cache_dir else config.cache_dir

    if not root.is_dir():
        return CacheInfo(repos=[], total_size=0, cache_dir=str(root))

    repos: list[CachedRepoInfo] = []
    total_size = 0

    for repo_type in _DEFAULT_SCAN_TYPES:
        segment = f"{repo_type}s"
        type_dir = root / segment
        if not type_dir.is_dir():
            continue

        for repo_dir in type_dir.iterdir():
            if not repo_dir.is_dir():
                continue

            # Compute size
            size = _dir_size(repo_dir)
            total_size += size

            # Count files
            nb_files = sum(1 for _ in repo_dir.rglob("*") if _.is_file())

            # Determine revision from snapshot dirs
            snapshots_dir = repo_dir / "snapshots"
            revision = None
            if snapshots_dir.is_dir():
                revisions = [d.name for d in snapshots_dir.iterdir() if d.is_dir()]
                revision = revisions[0] if len(revisions) == 1 else ",".join(revisions[:5])

            # Last access time
            try:
                last_accessed_ts = repo_dir.stat().st_atime
            except OSError:
                last_accessed_ts = 0

            # Decode repo_id from directory name (owner--name → owner/name)
            repo_id = repo_dir.name.replace("--", "/")

            repos.append(
                CachedRepoInfo(
                    repo_id=repo_id,
                    repo_type=repo_type,
                    revision=revision,
                    size_on_disk=size,
                    nb_files=nb_files,
                    last_accessed=last_accessed_ts if last_accessed_ts > 0 else None,
                    local_path=str(repo_dir),
                )
            )

    # Scan flat layout (compat): {root}/{owner}/{name}/
    # and legacy layout: {root}/hub/{owner}/{name}/
    _scanned_paths = {r.local_path for r in repos}  # avoid double-counting

    for prefix, prefix_path in [("", root), ("hub", root / "hub")]:
        if not prefix_path.is_dir():
            continue
        for owner_dir in prefix_path.iterdir():
            if not owner_dir.is_dir():
                continue
            # Skip known non-repo directories
            if owner_dir.name in ("hub", "models", "datasets", "studios", "mcps", "skills"):
                continue
            for name_dir in owner_dir.iterdir():
                if not name_dir.is_dir():
                    continue
                if str(name_dir) in _scanned_paths:
                    continue

                size = _dir_size(name_dir)
                total_size += size
                nb_files = sum(1 for f in name_dir.rglob("*") if f.is_file())
                repo_id = f"{owner_dir.name}/{name_dir.name}"

                repos.append(
                    CachedRepoInfo(
                        repo_id=repo_id,
                        repo_type=RepoType.MODEL,  # assume model for flat layout
                        revision=None,
                        size_on_disk=size,
                        nb_files=nb_files,
                        last_accessed=None,
                        local_path=str(name_dir),
                    )
                )

    return CacheInfo(
        repos=repos,
        total_size=total_size,
        cache_dir=str(root),
    )


def clear_cache(
    cache_dir: Path | None = None,
    repo_type: str | None = None,
    repo_id: str | None = None,
) -> int:
    """Remove cached data from disk.

    Parameters
    ----------
    cache_dir:
        Override for the cache directory. Defaults to the SDK config default.
    repo_type:
        If given, only clear caches of this repo type.
    repo_id:
        If given, only clear the cache for this specific repository.
        Must be used with ``repo_type``.

    Returns
    -------
    int
        Number of bytes freed.

    Raises
    ------
    CacheError
        On filesystem errors.
    """
    config = get_default_config()
    root = Path(cache_dir) if cache_dir else config.cache_dir

    # Guard against accidental nuke: passing only ``repo_id`` would otherwise
    # silently fall through to the "clear everything" branch below.
    if repo_id and not repo_type:
        raise CacheError("repo_type is required when repo_id is specified")

    if not root.is_dir():
        logger.info("Cache directory does not exist: %s", root)
        return 0

    freed = 0

    if repo_id and repo_type:
        # Clear specific repo — check all possible layout locations
        targets = _resolve_cache_targets(root, repo_id, repo_type)
        for target in targets:
            size = _dir_size(target)
            freed += size
            _safe_rmtree(target)
            logger.info("Cleared cache at %s (%d bytes)", target, size)
    elif repo_type:
        # Clear all repos of this type (standard layout)
        segment = f"{repo_type}s" if not repo_type.endswith("s") else repo_type
        type_dir = root / segment
        if type_dir.is_dir():
            size = _dir_size(type_dir)
            freed += size
            _safe_rmtree(type_dir)
            logger.info("Cleared %s standard cache (%d bytes)", repo_type, size)
        # Also clear legacy hub layout
        hub_dir = root / "hub"
        if hub_dir.is_dir():
            size = _dir_size(hub_dir)
            freed += size
            _safe_rmtree(hub_dir)
            logger.info("Cleared legacy hub cache (%d bytes)", size)
    else:
        # Clear everything (standard + legacy layouts)
        for repo_t in _DEFAULT_SCAN_TYPES:
            segment = f"{repo_t}s"
            type_dir = root / segment
            if type_dir.is_dir():
                freed += _dir_size(type_dir)
                _safe_rmtree(type_dir)
        # Legacy hub directory
        hub_dir = root / "hub"
        if hub_dir.is_dir():
            freed += _dir_size(hub_dir)
            _safe_rmtree(hub_dir)
        logger.info("Cleared all caches (%d bytes)", freed)

    return freed


def verify_cache(
    repo_id: str,
    repo_type: str,
    expected_by_path: dict[str, str | None],
    *,
    revision: str | None = None,
    cache_dir: str | Path | None = None,
    local_dir: str | Path | None = None,
) -> CacheVerification:
    """Compare a cached snapshot or local directory with remote SHA-256 values."""
    root, resolved_revision = _resolve_verification_root(
        repo_id,
        repo_type,
        revision=revision,
        cache_dir=cache_dir,
        local_dir=local_dir,
    )
    local_by_path = {
        relative.as_posix(): path
        for path in root.rglob("*")
        for relative in (path.relative_to(root),)
        if path.is_file() and not any(part.startswith(".") for part in relative.parts)
    }
    remote_paths = set(expected_by_path)
    local_paths = set(local_by_path)
    mismatches: list[VerificationMismatch] = []
    unverified: list[str] = []
    checked = 0

    for rel_path in sorted(remote_paths & local_paths):
        expected = expected_by_path[rel_path]
        if not expected:
            unverified.append(rel_path)
            continue
        checked += 1
        actual = compute_hash(local_by_path[rel_path], "sha256")
        if actual.lower() != expected.lower():
            mismatches.append(VerificationMismatch(rel_path, expected.lower(), actual.lower()))

    return CacheVerification(
        revision=resolved_revision,
        verified_path=str(root),
        checked_count=checked,
        mismatches=mismatches,
        missing_paths=sorted(remote_paths - local_paths),
        extra_paths=sorted(local_paths - remote_paths),
        unverified_paths=unverified,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_verification_root(
    repo_id: str,
    repo_type: str,
    *,
    revision: str | None,
    cache_dir: str | Path | None,
    local_dir: str | Path | None,
) -> tuple[Path, str]:
    if local_dir is not None:
        root = Path(local_dir).expanduser().resolve()
        if not root.is_dir():
            raise CacheError(f"Local directory does not exist: {root}")
        return root, revision or "master"

    cache_root = Path(cache_dir or get_default_config().cache_dir).expanduser().resolve()
    segment = f"{repo_type}s" if not repo_type.endswith("s") else repo_type
    repo_root = cache_root / segment / repo_id.replace("/", "--")
    snapshots = repo_root / "snapshots"
    if not snapshots.is_dir():
        raise CacheError(f"Repository is not present in cache: {repo_root}")

    if revision:
        snapshot = snapshots / revision
        if not snapshot.is_dir():
            raise CacheError(f"Revision '{revision}' is not present in cache: {snapshot}")
        return snapshot, revision

    for default_name in ("master", "main"):
        default_snapshot = snapshots / default_name
        if default_snapshot.is_dir():
            return default_snapshot, default_name
    candidates = sorted(path for path in snapshots.iterdir() if path.is_dir())
    if not candidates:
        raise CacheError(f"No cached revisions found in: {snapshots}")
    if len(candidates) == 1:
        return candidates[0], candidates[0].name
    raise CacheError("Cached revision is ambiguous; pass --revision explicitly")


def _resolve_cache_targets(root: Path, repo_id: str, repo_type: str) -> list[Path]:
    """Resolve all possible cache locations for a repo across layout formats.

    Checks three path layouts:
    - Standard:  {root}/{type}s/{owner}--{name}/
    - Flat:      {root}/{owner}/{name}/
    - Legacy:    {root}/hub/{owner}/{name}/
    """
    safe_id = repo_id.replace("/", "--")
    segment = f"{repo_type}s" if not repo_type.endswith("s") else repo_type

    candidates = [
        root / segment / safe_id,  # standard: {cache}/models/owner--name/
        root / repo_id,  # flat (compat): {cache}/owner/name/
        root / "hub" / repo_id,  # legacy: {cache}/hub/owner/name/
    ]
    return [p for p in candidates if p.is_dir()]


def _dir_size(path: Path) -> int:
    """Compute total size of all files under ``path`` recursively."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def _safe_rmtree(path: Path) -> None:
    """Remove a directory tree, raising CacheError on failure."""
    try:
        shutil.rmtree(path)
    except OSError as exc:
        raise CacheError(f"Failed to remove {path}: {exc}") from exc
