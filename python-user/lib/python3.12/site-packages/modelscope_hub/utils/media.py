"""Media file encoding utilities for Hub uploads."""

from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path

# Fallback MIME types for extensions not reliably resolved by the
# platform's mimetypes database (varies across OSes and Python versions).
_FALLBACK_MIME_TYPES: dict[str, str] = {
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".ico": "image/x-icon",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
}


def encode_media_to_base64(media_file_path: str | os.PathLike) -> str:
    """Encode a media file as a base64 data URL string.

    Returns a string of the form ``data:{mime_type};base64,{data}``.

    Raises:
        FileNotFoundError: if the path does not exist.
        ValueError: if the path is not a regular file or the MIME
            type cannot be determined.
    """
    path = Path(os.fspath(media_file_path)).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    mime_type, _ = mimetypes.guess_type(path.as_posix())
    if mime_type is None:
        mime_type = _FALLBACK_MIME_TYPES.get(path.suffix.lower())
    if mime_type is None:
        raise ValueError(
            f"Cannot determine MIME type for file: {path}"
        )

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


__all__ = ["encode_media_to_base64"]
