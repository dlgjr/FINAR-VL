"""Typed data containers returned by the SDK.

Every dataclass is constructible from a raw API payload via :func:`from_dict`,
which silently ignores fields the server may add in the future. This keeps the
client forward-compatible while still benefiting from static typing.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, Mapping, Type, TypedDict, TypeVar

from .constants import RepoType, Visibility

T = TypeVar("T")
_TDataclass = TypeVar("_TDataclass", bound="_FromDictMixin")


def _coerce_datetime(value: Any) -> datetime | None:
    """Best-effort conversion of an API timestamp into a :class:`datetime`."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        # ModelScope timestamps may arrive in seconds or milliseconds.
        seconds = value / 1000 if value > 1e12 else value
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


class _FromDictMixin:
    """Adds tolerant ``from_dict`` construction to a dataclass."""

    @classmethod
    def from_dict(cls: Type[_TDataclass], data: Mapping[str, Any] | None) -> _TDataclass:
        if not data:
            return cls()  # type: ignore[call-arg]
        known = {f.name for f in fields(cls)}  # type: ignore[arg-type]
        kwargs = {key: value for key, value in data.items() if key in known}
        return cls(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class UserInfo(_FromDictMixin):
    id: str | int | None = None
    username: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    description: str | None = None


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class RepoInfo(_FromDictMixin):
    id: str | int | None = None
    owner: str | None = None
    name: str | None = None
    repo_type: RepoType | str | None = None
    visibility: Visibility | int | None = None
    description: str | None = None
    downloads: int = 0
    likes: int = 0
    created_at: datetime | str | int | None = None
    last_modified: datetime | str | int | None = None
    license: str | None = None
    tags: list[str] = field(default_factory=list)
    # OpenAPI native fields
    display_name: str | None = None
    file_size: int | None = None
    tasks: list[str] = field(default_factory=list)
    private: bool | None = None
    gated: bool | None = None
    login_required: bool | None = None

    def __post_init__(self) -> None:
        if isinstance(self.repo_type, str):
            try:
                self.repo_type = RepoType(self.repo_type)
            except ValueError:
                pass
        if isinstance(self.visibility, int) and not isinstance(self.visibility, Visibility):
            try:
                self.visibility = Visibility(self.visibility)
            except ValueError:
                pass
        self.created_at = _coerce_datetime(self.created_at) or self.created_at
        self.last_modified = _coerce_datetime(self.last_modified) or self.last_modified

    def to_dict(self) -> dict:
        """Convert to OpenAPI-compatible dictionary.

        Excludes SDK-internal fields (owner, name, repo_type, visibility)
        and formats datetimes with Z suffix to match OpenAPI spec.
        """
        _INTERNAL_FIELDS = {"owner", "name", "repo_type", "visibility"}
        result = {}
        for f in fields(self):  # type: ignore[arg-type]
            if f.name in _INTERNAL_FIELDS:
                continue
            val = getattr(self, f.name)
            if val is None and f.name in ("display_name", "file_size", "private", "gated", "login_required"):
                continue  # skip None optional OpenAPI fields
            if isinstance(val, Enum):
                val = val.value
            elif isinstance(val, datetime):
                # OpenAPI uses Z suffix, not +00:00
                val = val.strftime("%Y-%m-%dT%H:%M:%SZ") if val.tzinfo else val.isoformat()
            elif isinstance(val, list):
                val = list(val)  # shallow copy
            result[f.name] = val
        return result

    @property
    def repo_id(self) -> str | None:
        """Canonical ``owner/name`` identifier, when both parts are known."""
        if self.owner and self.name:
            return f"{self.owner}/{self.name}"
        return None


# ---------------------------------------------------------------------------
# Files & commits
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class FileInfo(_FromDictMixin):
    path: str = ""
    size: int = 0
    blob_id: str | None = None
    type: str = "blob"  # "blob" | "tree"
    last_modified: datetime | str | int | None = None
    lfs: dict[str, Any] | None = None
    sha256: str | None = None

    def __post_init__(self) -> None:
        self.last_modified = _coerce_datetime(self.last_modified) or self.last_modified

    @property
    def is_dir(self) -> bool:
        return self.type == "tree"

    @property
    def is_lfs(self) -> bool:
        return self.lfs is not None


@dataclass(slots=True)
class CommitInfo(_FromDictMixin):
    sha: str = ""
    message: str = ""
    author: str | None = None
    date: datetime | str | int | None = None

    def __post_init__(self) -> None:
        self.date = _coerce_datetime(self.date) or self.date


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class PagedResult(Generic[T]):
    items: list[T] = field(default_factory=list)
    total_count: int = 0
    page_number: int = 1
    page_size: int = 0
    collection_key: str = field(default="items", repr=False)

    @property
    def has_next(self) -> bool:
        if self.page_size <= 0:
            return False
        return self.page_number * self.page_size < self.total_count

    def to_dict(self) -> dict:
        """Convert to OpenAPI-compatible dictionary.

        Uses collection_key for the items array name (e.g. 'datasets', 'models').
        """
        return {
            self.collection_key: [item.to_dict() if hasattr(item, "to_dict") else item for item in self.items],
            "total_count": self.total_count,
            "page_number": self.page_number,
            "page_size": self.page_size,
        }

    def __iter__(self):  # pragma: no cover - convenience iteration
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class CachedRepoInfo(_FromDictMixin):
    repo_id: str = ""
    repo_type: RepoType | str | None = None
    revision: str | None = None
    size_on_disk: int = 0
    nb_files: int = 0
    last_accessed: datetime | str | int | None = None
    local_path: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.repo_type, str):
            try:
                self.repo_type = RepoType(self.repo_type)
            except ValueError:
                pass
        self.last_accessed = _coerce_datetime(self.last_accessed) or self.last_accessed


@dataclass(slots=True)
class CacheInfo:
    repos: list[CachedRepoInfo] = field(default_factory=list)
    total_size: int = 0
    cache_dir: str | None = None

    @property
    def total_repos(self) -> int:
        return len(self.repos)


@dataclass(slots=True)
class VerificationMismatch:
    path: str
    expected: str
    actual: str
    algorithm: str = "sha256"


@dataclass(slots=True)
class CacheVerification:
    """Result of comparing local repository files with Hub checksums."""

    revision: str
    verified_path: str
    checked_count: int = 0
    mismatches: list[VerificationMismatch] = field(default_factory=list)
    missing_paths: list[str] = field(default_factory=list)
    extra_paths: list[str] = field(default_factory=list)
    unverified_paths: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# TypedDict payloads (for OpenAPI method signatures)
# ---------------------------------------------------------------------------
class CreateSkillPayload(TypedDict, total=False):
    """Payload for creating a new skill via POST /skills."""

    skill_name: str
    owner: str
    display_name: str
    source_url: str
    private: bool
    description: str
    license: str
    category: str
    tags: list[str]
    logo_url: str
    skill_file: str


class UpdateSkillSettingsPayload(TypedDict, total=False):
    """Payload for updating skill settings via PATCH /skills/{owner}/{skill_name}/settings."""

    display_name: str
    source_url: str
    private: bool
    description: str
    license: str
    category: str
    tags: list[str]
    logo_url: str
    skill_file: str


class CreateStudioPayload(TypedDict, total=False):
    """Payload for creating a new studio via POST /studios."""

    repo_name: str
    owner: str
    display_name: str
    license: str
    private: bool
    description: str
    coverImage: str
    sdk_type: str
    sdk_version: str
    base_image: str
    hardware: str


class UpdateStudioSettingsPayload(TypedDict, total=False):
    """Payload for updating studio settings via PATCH /studios/{owner}/{repo_name}/settings."""

    display_name: str
    license: str
    private: bool
    description: str
    coverImage: str
    sdk_type: str
    sdk_version: str
    base_image: str
    hardware: str


class DeployMcpServerPayload(TypedDict, total=False):
    """Payload for deploying an MCP server via POST /mcp/servers/{id}/deploy."""

    transport_type: str
    expiration_minutes: int
    auth_check: bool
    env_info: dict[str, str]


__all__ = [
    "CacheVerification",
    "CacheInfo",
    "CachedRepoInfo",
    "CommitInfo",
    "CreateSkillPayload",
    "CreateStudioPayload",
    "DeployMcpServerPayload",
    "FileInfo",
    "PagedResult",
    "RepoInfo",
    "UpdateSkillSettingsPayload",
    "UpdateStudioSettingsPayload",
    "UserInfo",
    "VerificationMismatch",
]
