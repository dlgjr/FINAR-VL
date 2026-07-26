"""Filesystem helpers used by the cache, download and upload subsystems."""

from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
from typing import IO, Union

from ..constants import DEFAULT_CACHE_DIR_NAME, DOWNLOAD_CHUNK_SIZE, ENV_CACHE
from ..errors import FileIntegrityError

PathLike = Union[str, os.PathLike[str], Path]
FileObj = Union[IO[bytes], io.IOBase]


def compute_hash(
    file_path: PathLike,
    algorithm: str = "sha256",
    *,
    chunk_size: int = DOWNLOAD_CHUNK_SIZE,
) -> str:
    """Compute a hex digest of ``file_path`` using ``algorithm``.

    Parameters
    ----------
    file_path:
        Path of the file to hash.
    algorithm:
        Any algorithm accepted by :func:`hashlib.new` (e.g. ``"sha256"``,
        ``"sha1"``, ``"md5"``).
    chunk_size:
        Read buffer size in bytes.

    Raises
    ------
    FileIntegrityError
        If ``file_path`` is missing or the algorithm is unsupported.
    """
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")
    path = Path(file_path)
    if not path.is_file():
        raise FileIntegrityError(f"Cannot hash non-existent file: {path}")
    try:
        hasher = hashlib.new(algorithm)
    except (ValueError, TypeError) as exc:
        raise FileIntegrityError(f"Unsupported hash algorithm: {algorithm!r}") from exc

    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_file_size(path_or_fileobj: PathLike | FileObj) -> int:
    """Return the size in bytes of either a path or an open binary file object."""
    if isinstance(path_or_fileobj, (str, os.PathLike, Path)):
        return Path(path_or_fileobj).stat().st_size

    fobj = path_or_fileobj
    # Prefer fstat for real files — works without side effects on the cursor.
    try:
        fileno = fobj.fileno()  # type: ignore[union-attr]
        return os.fstat(fileno).st_size
    except (AttributeError, OSError, io.UnsupportedOperation):
        pass

    if not hasattr(fobj, "seek") or not hasattr(fobj, "tell"):
        raise TypeError("File-like object must support seek/tell to determine size")

    current = fobj.tell()
    try:
        fobj.seek(0, os.SEEK_END)
        return fobj.tell()
    finally:
        fobj.seek(current)


def get_cache_dir() -> Path:
    """Return the SDK cache directory, honouring ``MODELSCOPE_CACHE``."""
    override = os.environ.get(ENV_CACHE)
    if override:
        return ensure_dir(override)
    return ensure_dir(Path.home() / ".cache" / DEFAULT_CACHE_DIR_NAME)


def ensure_dir(path: PathLike) -> Path:
    """Create ``path`` (and parents) if missing and return it as :class:`Path`."""
    p = Path(path).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


__all__ = [
    "compute_hash",
    "ensure_dir",
    "get_cache_dir",
    "get_file_size",
]
