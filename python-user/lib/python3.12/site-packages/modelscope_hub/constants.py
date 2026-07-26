"""Project-wide constants and configuration knobs.

All runtime tunables expose an environment-variable override so that the SDK
can be reconfigured without code changes. This keeps the library friendly for
both production deployments and ad-hoc experimentation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum, IntEnum


# ---------------------------------------------------------------------------
# StrEnum compatibility shim (Python 3.10 lacks :class:`enum.StrEnum`).
# ---------------------------------------------------------------------------
try:  # pragma: no cover - exercised implicitly by the import path
    from enum import StrEnum  # type: ignore[attr-defined]
except ImportError:  # Python 3.10
    class StrEnum(str, Enum):  # type: ignore[no-redef]
        """Minimal backport of :class:`enum.StrEnum` for Python 3.10."""

        def __str__(self) -> str:  # noqa: D401 - mirror stdlib behaviour
            return str(self.value)


# ---------------------------------------------------------------------------
# Centralised environment-variable registry
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class EnvVar:
    """Metadata for one configurable environment variable."""

    name: str
    default: str
    description: str
    category: str  # Core, Network, Download, Upload, Logging, Deprecated
    deprecated_names: tuple[str, ...] = ()

ENV_REGISTRY: list[EnvVar] = []

CATEGORY_ORDER: tuple[str, ...] = (
    "Core", "Network", "Download", "Upload", "Logging", "Deprecated",
)


# ---------------------------------------------------------------------------
# Domain enums
# ---------------------------------------------------------------------------
class RepoType(StrEnum):
    """Kinds of repositories hosted on ModelScope Hub."""

    MODEL = "model"
    DATASET = "dataset"
    STUDIO = "studio"
    SKILL = "skill"
    MCP = "mcp"


class Visibility(IntEnum):
    """Repository visibility levels.

    The integer values mirror the encoding used by the ModelScope Hub API
    (1 = private, 3 = internal, 5 = public).
    """

    PRIVATE = 1
    INTERNAL = 3
    PUBLIC = 5

    @property
    def label(self) -> str:
        """Human readable label."""
        return self.name.lower()

    @classmethod
    def from_label(cls, label: str) -> "Visibility":
        """Resolve a visibility from its lowercase label or numeric string.

        Supports both label strings ('private', 'internal', 'public') and
        numeric strings ('1', '3', '5') for backward compatibility.
        """
        # Support numeric strings for backward compatibility: '1' → PRIVATE, '3' → INTERNAL, '5' → PUBLIC
        if isinstance(label, str) and label.isdigit():
            numeric = int(label)
            for member in cls:
                if member.value == numeric:
                    return member
            raise ValueError(f"Unknown visibility label: {label!r}")
        # Standard label lookup: 'private' → PRIVATE
        try:
            return cls[label.upper()]
        except KeyError as exc:
            raise ValueError(f"Unknown visibility label: {label!r}") from exc


class License(StrEnum):
    """Common open-source licenses used on ModelScope Hub."""

    APACHE_2_0 = "Apache-2.0"
    MIT = "MIT"
    BSD_2_CLAUSE = "BSD-2-Clause"
    BSD_3_CLAUSE = "BSD-3-Clause"
    GPL_2_0 = "GPL-2.0"
    GPL_3_0 = "GPL-3.0"
    LGPL_2_1 = "LGPL-2.1"
    LGPL_3_0 = "LGPL-3.0"
    MPL_2_0 = "MPL-2.0"
    CC_BY_4_0 = "CC-BY-4.0"
    CC_BY_SA_4_0 = "CC-BY-SA-4.0"
    CC_BY_NC_4_0 = "CC-BY-NC-4.0"
    CC0_1_0 = "CC0-1.0"
    UNLICENSE = "Unlicense"
    OTHER = "Other"


# ---------------------------------------------------------------------------
# Endpoint configuration
# ---------------------------------------------------------------------------
DEFAULT_ENDPOINT: str = "https://modelscope.cn"
OPENAPI_PREFIX: str = "/openapi/v1"
LEGACY_API_PREFIX: str = "/api/v1"


# ---------------------------------------------------------------------------
# Helpers for environment-driven overrides (auto-registering)
# ---------------------------------------------------------------------------
_REGISTERED_NAMES: set[str] = set()
_DEPRECATED_LOOKUP: dict[str, tuple[str, ...]] = {}


def _env(name: str, *deprecated_names: str) -> str | None:
    """Read an env var, falling back to deprecated names with a warning."""
    value = os.environ.get(name)
    if value is not None:
        return value
    for old in deprecated_names:
        value = os.environ.get(old)
        if value is not None:
            import warnings
            warnings.warn(
                f"Environment variable {old!r} is deprecated, "
                f"use {name!r} instead.",
                FutureWarning,
                stacklevel=4,
            )
            return value
    return None


def _env_int(
    name: str,
    default: int,
    description: str = "",
    category: str = "",
    *deprecated_names: str,
) -> int:
    """Read a positive integer from the environment and register it."""
    all_deprecated = deprecated_names or _DEPRECATED_LOOKUP.get(name, ())
    if description and category:
        _env_register(name, str(default), description, category,
                      deprecated_names=all_deprecated)
    raw = _env(name, *all_deprecated)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _env_int_mb(
    name: str,
    default_mb: int,
    description: str = "",
    category: str = "",
    *deprecated_byte_names: str,
) -> int:
    """Read a size env var (new name in MB, deprecated names in bytes). Returns bytes.

    Handles migration from byte-based deprecated env vars to MB-based new names.
    If a deprecated byte-based name is set, the value is used directly (already bytes).
    If the new name is set, the value is treated as MB and converted to bytes.
    """
    all_deprecated = deprecated_byte_names or _DEPRECATED_LOOKUP.get(name, ())
    if description and category:
        _env_register(name, str(default_mb), description, category,
                      deprecated_names=all_deprecated)
    # Check the new name first (value in MB)
    raw = os.environ.get(name)
    if raw is not None and raw.strip():
        try:
            value = int(raw)
        except ValueError:
            return default_mb * 1024 * 1024
        return value * 1024 * 1024 if value > 0 else default_mb * 1024 * 1024
    # Fall back to deprecated names (value already in bytes)
    for old in all_deprecated:
        raw = os.environ.get(old)
        if raw is not None and raw.strip():
            import warnings
            warnings.warn(
                f"Environment variable {old!r} is deprecated, "
                f"use {name!r} instead. Note: {name!r} expects a value in MB.",
                FutureWarning,
                stacklevel=2,
            )
            try:
                value = int(raw)
            except ValueError:
                return default_mb * 1024 * 1024
            return value if value > 0 else default_mb * 1024 * 1024
    return default_mb * 1024 * 1024


def _env_bool(
    name: str,
    default: bool,
    description: str = "",
    category: str = "",
    *deprecated_names: str,
) -> bool:
    """Read a boolean from the environment and register it."""
    if description and category:
        _env_register(name, str(default).lower(), description, category,
                      deprecated_names=deprecated_names)
    all_deprecated = deprecated_names or _DEPRECATED_LOOKUP.get(name, ())
    raw = _env(name, *all_deprecated)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_register(
    name: str,
    default: str,
    description: str,
    category: str,
    *,
    deprecated_names: tuple[str, ...] = (),
) -> None:
    """Register an env var for display only (read logic lives elsewhere)."""
    if category not in CATEGORY_ORDER:
        raise ValueError(f"Unknown env var category {category!r}, must be one of {CATEGORY_ORDER}")
    if name in _REGISTERED_NAMES:
        return
    _REGISTERED_NAMES.add(name)
    if deprecated_names:
        _DEPRECATED_LOOKUP[name] = deprecated_names
    ENV_REGISTRY.append(EnvVar(name, default, description, category, deprecated_names))


# ---------------------------------------------------------------------------
# Core env vars (read logic in config.py / HubConfig)
# ---------------------------------------------------------------------------
_env_register("MODELSCOPE_API_TOKEN", "-", "API authentication token", "Core")
_env_register("MODELSCOPE_ENDPOINT", DEFAULT_ENDPOINT, "API endpoint URL", "Core")
_env_register("MODELSCOPE_CACHE", "~/.cache/modelscope", "Local cache directory", "Core")
ENV_CACHE: str = "MODELSCOPE_CACHE"
_env_register("MODELSCOPE_HOME", "~/.modelscope", "SDK config directory", "Core")


# ---------------------------------------------------------------------------
# Network / IO tunables
# ---------------------------------------------------------------------------
API_TIMEOUT: int = _env_int(
    "MODELSCOPE_API_TIMEOUT", 60,
    "HTTP request timeout (seconds)", "Network",
    "API_TIMEOUT",
)

API_CONNECT_TIMEOUT: int = _env_int(
    "MODELSCOPE_API_CONNECT_TIMEOUT", 10,
    "HTTP connect timeout (seconds)", "Network",
)

API_MAX_RETRIES: int = _env_int(
    "MODELSCOPE_API_MAX_RETRIES", 5,
    "Max retry attempts for transient failures", "Network",
    "API_MAX_RETRIES",
)

# ---------------------------------------------------------------------------
# Endpoint switching
# ---------------------------------------------------------------------------
ENV_MODELSCOPE_DOMAIN: str = "MODELSCOPE_DOMAIN"
_env_register(ENV_MODELSCOPE_DOMAIN, "-", "Deprecated: use MODELSCOPE_ENDPOINT", "Deprecated")

ENV_PREFER_AI_SITE: str = "MODELSCOPE_PREFER_AI_SITE"
_env_register(ENV_PREFER_AI_SITE, "false", "Prefer modelscope.ai over modelscope.cn", "Core")

DEFAULT_INTL_ENDPOINT: str = "https://www.modelscope.ai"
"""International site endpoint."""

# ---------------------------------------------------------------------------
# Download tunables
# ---------------------------------------------------------------------------
DOWNLOAD_CHUNK_SIZE: int = _env_int_mb(
    "MODELSCOPE_DOWNLOAD_CHUNK_SIZE_MB", 1,
    "Streaming chunk size (MB)", "Download",
    "DOWNLOAD_CHUNK_SIZE",
)

DOWNLOAD_PARALLEL_THRESHOLD: int = _env_int(
    "MODELSCOPE_DOWNLOAD_PARALLEL_THRESHOLD_MB", 500,
    "Parallel download threshold (MB)", "Download",
    "MODELSCOPE_PARALLEL_DOWNLOAD_THRESHOLD_MB",
) * 1024 * 1024

DOWNLOAD_PARALLELS: int = _env_int(
    "MODELSCOPE_DOWNLOAD_PARALLEL_WORKERS", 1,
    "Parallel range-download streams", "Download",
    "MODELSCOPE_DOWNLOAD_PARALLELS",
)

DOWNLOAD_RETRY_TIMES: int = _env_int(
    "MODELSCOPE_DOWNLOAD_MAX_RETRIES", 5,
    "Per-file download retry count", "Download",
    "DOWNLOAD_RETRY_TIMES",
)

DOWNLOAD_TIMEOUT: int = _env_int(
    "MODELSCOPE_DOWNLOAD_TIMEOUT", 60,
    "Per-file download timeout (seconds)", "Download",
    "DOWNLOAD_TIMEOUT",
)

DOWNLOAD_PART_SIZE: int = _env_int_mb(
    "MODELSCOPE_DOWNLOAD_PART_SIZE_MB", 160,
    "Parallel range chunk size (MB)", "Download",
    "DOWNLOAD_PART_SIZE",
)

TEMPORARY_FOLDER_NAME: str = "._____temp"
"""Temporary folder name used during downloads."""

FILE_HASH_FIELD: str = "Sha256"
"""API response field name for file hash."""

ENV_FILE_LOCK: str = "MODELSCOPE_DOWNLOAD_FILE_LOCK"
_env_register(ENV_FILE_LOCK, "true", "File lock for multiprocess download safety", "Download",
              deprecated_names=("MODELSCOPE_HUB_FILE_LOCK",))

ENV_INTRA_CLOUD_ACCELERATION: str = "MODELSCOPE_DOWNLOAD_INTRA_CLOUD"
_env_register(ENV_INTRA_CLOUD_ACCELERATION, "true", "Alibaba cloud intra-cloud acceleration", "Download",
              deprecated_names=("INTRA_CLOUD_ACCELERATION",))

ENV_INTRA_CLOUD_REGION: str = "MODELSCOPE_DOWNLOAD_INTRA_CLOUD_REGION"
_env_register(ENV_INTRA_CLOUD_REGION, "(auto)", "Override intra-cloud region ID", "Download",
              deprecated_names=("INTRA_CLOUD_ACCELERATION_REGION",))

ENV_INTER_CLOUD_REGIONS: str = "MODELSCOPE_DOWNLOAD_INTER_CLOUD_REGIONS"
_env_register(ENV_INTER_CLOUD_REGIONS, "",
              "Comma-separated peer regions for cross-region internal acceleration", "Download")

UPLOAD_LFS_THRESHOLD: int = _env_int("UPLOAD_LFS_THRESHOLD", 5 * 1024 * 1024)
UPLOAD_LFS_ENFORCE_THRESHOLD: int = _env_int("UPLOAD_LFS_ENFORCE_THRESHOLD", 1 * 1024 * 1024)

# Upload: blob retry
UPLOAD_BLOB_MAX_RETRIES: int = _env_int("UPLOAD_BLOB_MAX_RETRIES", 5)
UPLOAD_BLOB_RETRY_BACKOFF: int = _env_int("UPLOAD_BLOB_RETRY_BACKOFF", 2)
UPLOAD_BLOB_RETRY_MAX_WAIT: int = _env_int("UPLOAD_BLOB_RETRY_MAX_WAIT", 60)
UPLOAD_BLOB_TQDM_DISABLE_THRESHOLD: int = _env_int("UPLOAD_BLOB_TQDM_DISABLE_THRESHOLD", 5 * 1024 * 1024)

# Upload: blob timeout
UPLOAD_BLOB_CONNECT_TIMEOUT: int = _env_int(
    "MODELSCOPE_UPLOAD_CONNECT_TIMEOUT", 30,
    "Upload connect timeout (seconds)", "Upload",
    "UPLOAD_BLOB_CONNECT_TIMEOUT",
)
UPLOAD_BLOB_READ_TIMEOUT: int = _env_int(
    "MODELSCOPE_UPLOAD_READ_TIMEOUT", 3600,
    "Upload read timeout (seconds)", "Upload",
    "UPLOAD_BLOB_READ_TIMEOUT",
)

# Upload: urllib3 retry
UPLOAD_RETRY_ALLOWED_METHODS: frozenset[str] = frozenset(
    os.environ.get(
        "UPLOAD_RETRY_ALLOWED_METHODS", "GET,HEAD,DELETE,OPTIONS,TRACE"
    ).split(",")
)

# Upload: batching
UPLOAD_COMMIT_BATCH_SIZE: int = _env_int("UPLOAD_COMMIT_BATCH_SIZE", 256)
UPLOAD_ADAPTIVE_BATCH_SIZE: bool = _env_bool("UPLOAD_ADAPTIVE_BATCH_SIZE", True)
UPLOAD_VALIDATE_BLOB_BATCH_SIZE: int = _env_int("UPLOAD_VALIDATE_BLOB_BATCH_SIZE", 64)

# Upload: commit retry
UPLOAD_COMMIT_MAX_RETRIES: int = _env_int("UPLOAD_COMMIT_MAX_RETRIES", 5)
UPLOAD_COMMIT_MAX_TOTAL_WAIT: int = _env_int(
    "MODELSCOPE_UPLOAD_COMMIT_MAX_TOTAL_WAIT",
    300,
    "Maximum total wait time (seconds) for commit retries in _commit_with_retry",
    "Upload",
)

# Upload: consecutive batch failure limit
UPLOAD_BATCH_CONSECUTIVE_FAILURE_LIMIT: int = _env_int(
    "MODELSCOPE_UPLOAD_BATCH_CONSECUTIVE_FAILURE_LIMIT",
    3,
    "Maximum consecutive batch commit failures before aborting upload_folder",
    "Upload",
)

# Upload: failed file retry & ReAct
UPLOAD_FAILED_FILE_MAX_RETRIES: int = _env_int("UPLOAD_FAILED_FILE_MAX_RETRIES", 3)
UPLOAD_REACT_ENABLED: bool = _env_bool("UPLOAD_REACT_ENABLED", True)
UPLOAD_REACT_ROUND2_BASE_DELAY: int = _env_int("UPLOAD_REACT_ROUND2_BASE_DELAY", 2)
UPLOAD_REACT_ROUND3_FILE_DELAY: int = _env_int("UPLOAD_REACT_ROUND3_FILE_DELAY", 5)
UPLOAD_REACT_BACKOFF_MAX_EXPONENT: int = _env_int("UPLOAD_REACT_BACKOFF_MAX_EXPONENT", 5)
UPLOAD_REACT_MAX_DELAY: int = _env_int("UPLOAD_REACT_MAX_DELAY", 120)

# Upload: workers
DEFAULT_MAX_WORKERS: int = _env_int(
    "MODELSCOPE_UPLOAD_MAX_WORKERS", min(8, (os.cpu_count() or 4) + 4),
    "Default parallel worker threads (min(8, cpu+4))", "Upload",
    "DEFAULT_MAX_WORKERS",
)

# Upload: cache / tracker
UPLOAD_USE_CACHE: bool = _env_bool(
    "MODELSCOPE_UPLOAD_CACHE", True,
    "Enable resumable upload cache", "Upload",
    "UPLOAD_USE_CACHE",
)
UPLOAD_CACHE_FILE: str = ".ms_upload_cache"
UPLOAD_LEGACY_PROGRESS_FILE: str = ".ms_upload_progress"

# Upload: limits
UPLOAD_MAX_FILE_SIZE: int = _env_int_mb(
    "MODELSCOPE_UPLOAD_MAX_FILE_SIZE_MB", 100 * 1024,
    "Max single file size (MB, default 100 GB)", "Upload",
    "UPLOAD_MAX_FILE_SIZE",
)
UPLOAD_MAX_FILE_COUNT: int = _env_int(
    "MODELSCOPE_UPLOAD_MAX_FILE_COUNT", 100_000,
    "Max total files per upload", "Upload",
    "UPLOAD_MAX_FILE_COUNT",
)
UPLOAD_MAX_FILE_COUNT_IN_DIR: int = _env_int("UPLOAD_MAX_FILE_COUNT_IN_DIR", 50_000)
UPLOAD_NORMAL_FILE_SIZE_TOTAL_LIMIT: int = _env_int("UPLOAD_NORMAL_FILE_SIZE_TOTAL_LIMIT", 500 * 1024 * 1024)

# LFS suffix lists (from old SDK — determines upload mode regardless of size)
MODEL_LFS_SUFFIX: list[str] = [
    ".7z", ".arrow", ".bin", ".bz2", ".ckpt", ".ftz", ".gz", ".h5",
    ".joblib", ".mlmodel", ".model", ".msgpack", ".npy", ".npz", ".onnx",
    ".ot", ".parquet", ".pb", ".pickle", ".pkl", ".pt", ".pth", ".rar",
    ".safetensors", ".tar", ".tflite", ".tgz", ".wasm", ".xz", ".zip", ".zst",
]
DATASET_LFS_SUFFIX: list[str] = [
    ".7z", ".aac", ".arrow", ".audio", ".bmp", ".bin", ".bz2", ".flac",
    ".ftz", ".gif", ".gz", ".h5", ".jack", ".jpeg", ".jpg", ".png", ".jsonl",
    ".joblib", ".lz4", ".msgpack", ".npy", ".npz", ".ot", ".parquet", ".pb",
    ".pickle", ".pcm", ".pkl", ".raw", ".rar", ".sam", ".tar", ".tgz",
    ".wasm", ".wav", ".webm", ".webp", ".zip", ".zst", ".tiff", ".mp3",
    ".mp4", ".ogg",
]

# Default ignore patterns for folder upload
DEFAULT_IGNORE_PATTERNS: list[str] = [
    ".git", ".git/*", "*/.git", "**/.git/**",
    ".cache", ".cache/*", "*/.cache", "**/.cache/**",
]


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
MODELSCOPE_ASCII = r"""
 _   .-')                _ .-') _     ('-.             .-')                              _ (`-.    ('-.
( '.( OO )_             ( (  OO) )  _(  OO)           ( OO ).                           ( (OO  ) _(  OO)
 ,--.   ,--.).-'),-----. \     .'_ (,------.,--.     (_)---\_)   .-----.  .-'),-----.  _.`     \(,------.
 |   `.'   |( OO'  .-.  ',`'--..._) |  .---'|  |.-') /    _ |   '  .--./ ( OO'  .-.  '(__...--'' |  .---'
 |         |/   |  | |  ||  |  \  ' |  |    |  | OO )\  :` `.   |  |('-. /   |  | |  | |  /  | | |  |
 |  |'.'|  |\_) |  |\|  ||  |   ' |(|  '--. |  |`-' | '..`''.) /_) |OO  )\_) |  |\|  | |  |_.' |(|  '--.
 |  |   |  |  \ |  | |  ||  |   / : |  .--'(|  '---.'.-._)   \ ||  |`-'|   \ |  | |  | |  .___.' |  .--'
 |  |   |  |   `'  '-'  '|  '--'  / |  `---.|      | \       /(_'  '--'\    `'  '-'  ' |  |      |  `---.
 `--'   `--'     `-----' `-------'  `------'`------'  `-----'    `-----'      `-----'  `--'      `------'
"""  # noqa: E501


# ---------------------------------------------------------------------------
# Logging / deprecated (read logic in utils/logger.py, cli/compat.py)
# ---------------------------------------------------------------------------
_env_register("MODELSCOPE_LOG_LEVEL", "INFO", "SDK log level (DEBUG/INFO/WARNING/ERROR)", "Logging")
_env_register("MODELSCOPE_NO_DEPRECATION_WARNINGS", "-", "Suppress deprecation warnings", "Logging",
              deprecated_names=("MODELSCOPE_HUB_NO_DEPRECATION_WARNINGS",))


# ---------------------------------------------------------------------------
# Filesystem layout
# ---------------------------------------------------------------------------
DEFAULT_CACHE_DIR_NAME: str = "modelscope"
SESSION_FILE_NAME: str = "session"
CONFIG_DIR_NAME: str = ".modelscope"
CREDENTIALS_DIR_NAME: str = "credentials"
COOKIES_FILE_NAME: str = "cookies"
GIT_TOKEN_FILE_NAME: str = "git_token"
USER_INFO_FILE_NAME: str = "user"


__all__ = [
    "API_CONNECT_TIMEOUT",
    "API_MAX_RETRIES",
    "API_TIMEOUT",
    "CATEGORY_ORDER",
    "CONFIG_DIR_NAME",
    "DATASET_LFS_SUFFIX",
    "DEFAULT_CACHE_DIR_NAME",
    "DEFAULT_ENDPOINT",
    "DEFAULT_IGNORE_PATTERNS",
    "DEFAULT_INTL_ENDPOINT",
    "DEFAULT_MAX_WORKERS",
    "DOWNLOAD_CHUNK_SIZE",
    "DOWNLOAD_PARALLEL_THRESHOLD",
    "DOWNLOAD_PARALLELS",
    "DOWNLOAD_PART_SIZE",
    "DOWNLOAD_RETRY_TIMES",
    "DOWNLOAD_TIMEOUT",
    "ENV_FILE_LOCK",
    "ENV_CACHE",
    "ENV_INTRA_CLOUD_ACCELERATION",
    "ENV_INTRA_CLOUD_REGION",
    "ENV_INTER_CLOUD_REGIONS",
    "ENV_MODELSCOPE_DOMAIN",
    "ENV_PREFER_AI_SITE",
    "ENV_REGISTRY",
    "EnvVar",
    "FILE_HASH_FIELD",
    "LEGACY_API_PREFIX",
    "License",
    "MODEL_LFS_SUFFIX",
    "OPENAPI_PREFIX",
    "RepoType",
    "StrEnum",
    "SESSION_FILE_NAME",
    "TEMPORARY_FOLDER_NAME",
    "UPLOAD_ADAPTIVE_BATCH_SIZE",
    "UPLOAD_BLOB_CONNECT_TIMEOUT",
    "UPLOAD_BLOB_MAX_RETRIES",
    "UPLOAD_BLOB_READ_TIMEOUT",
    "UPLOAD_BLOB_RETRY_BACKOFF",
    "UPLOAD_BLOB_RETRY_MAX_WAIT",
    "UPLOAD_BLOB_TQDM_DISABLE_THRESHOLD",
    "UPLOAD_CACHE_FILE",
    "UPLOAD_COMMIT_BATCH_SIZE",
    "UPLOAD_BATCH_CONSECUTIVE_FAILURE_LIMIT",
    "UPLOAD_COMMIT_MAX_RETRIES",
    "UPLOAD_COMMIT_MAX_TOTAL_WAIT",
    "UPLOAD_FAILED_FILE_MAX_RETRIES",
    "UPLOAD_LEGACY_PROGRESS_FILE",
    "UPLOAD_LFS_ENFORCE_THRESHOLD",
    "UPLOAD_LFS_THRESHOLD",
    "UPLOAD_MAX_FILE_COUNT",
    "UPLOAD_MAX_FILE_COUNT_IN_DIR",
    "UPLOAD_MAX_FILE_SIZE",
    "UPLOAD_NORMAL_FILE_SIZE_TOTAL_LIMIT",
    "UPLOAD_REACT_BACKOFF_MAX_EXPONENT",
    "UPLOAD_REACT_ENABLED",
    "UPLOAD_REACT_MAX_DELAY",
    "UPLOAD_REACT_ROUND2_BASE_DELAY",
    "UPLOAD_REACT_ROUND3_FILE_DELAY",
    "UPLOAD_RETRY_ALLOWED_METHODS",
    "UPLOAD_USE_CACHE",
    "UPLOAD_VALIDATE_BLOB_BATCH_SIZE",
    "Visibility",
]
