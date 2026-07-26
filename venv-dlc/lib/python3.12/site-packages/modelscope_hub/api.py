"""High-level public API facade for the ModelScope Hub SDK.

:class:`HubApi` is the **only** entry point users should construct. It composes
the low-level :class:`OpenAPIClient`, :class:`LegacyClient`,
:class:`DownloadManager`, :class:`UploadManager` and the cache helpers into a
unified, OpenAPI-first surface.

Design principles
-----------------
* **OpenAPI-first** — every operation that has an OpenAPI counterpart goes
  through :mod:`._openapi`. Legacy endpoints are used only as a transparent
  fallback when no OpenAPI equivalent exists.
* **Unified repo pattern** — every repository operation accepts a
  ``repo_type`` parameter; there are no type-specific methods like
  ``create_model`` or ``get_dataset``.
* **Transparent fallback** — callers do not need to know which path served
  their request.
* **Lazy clients** — the underlying HTTP clients are instantiated on demand
  so that ``HubApi()`` never fails just because no token is present.
* **SOLID** — :class:`HubApi` only routes and orchestrates; concrete network
  logic lives in the injected dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO, Iterable, Mapping
from urllib.parse import urlparse

from requests.cookies import RequestsCookieJar

from ._cache_manager import clear_cache as _clear_cache
from ._cache_manager import _resolve_verification_root
from ._cache_manager import scan_cache as _scan_cache
from ._download import DownloadManager, ProgressCallback
from ._cache_manager import verify_cache as _verify_cache
from ._download import DownloadManager
from ._legacy_api import LegacyClient
from ._openapi import OpenAPIClient
from ._upload import UploadManager
from .config import HubConfig, get_default_config
from .constants import RepoType, Visibility
from .errors import (
    AuthenticationError,
    HubError,
    InvalidParameter,
    NetworkError,
    NotExistError,
    NotSupportedError,
)
from .types import CacheInfo, CacheVerification, FileInfo, PagedResult, RepoInfo, UserInfo
from .utils.logger import get_logger

__all__ = ["HubApi"]

logger = get_logger("api")

RepoTypeLike = "str | RepoType"


# Routing tables — declarative dispatch keeps :class:`HubApi` free of long
# if/elif chains and makes adding new repo types a one-line change.
_CREATABLE_TYPES: frozenset[RepoType] = frozenset({RepoType.MODEL, RepoType.DATASET, RepoType.STUDIO, RepoType.SKILL})
_OPENAPI_CREATE_TYPES: frozenset[RepoType] = frozenset({RepoType.STUDIO, RepoType.SKILL})
_OPENAPI_DETAIL_TYPES: frozenset[RepoType] = frozenset(
    {RepoType.MODEL, RepoType.DATASET, RepoType.STUDIO, RepoType.SKILL}
)
# Mapping of common license display names to their SPDX identifiers. The Hub
# backend rejects display names like ``"Apache License 2.0"`` — we translate
# them transparently while passing unknown values (already SPDX) through.
_LICENSE_DISPLAY_TO_SPDX: dict[str, str] = {
    "Apache License 2.0": "apache-2.0",
    "MIT License": "mit",
    "GPL-2.0": "gpl-2.0",
    "GPL-3.0": "gpl-3.0",
    "LGPL-2.1": "lgpl-2.1",
    "LGPL-3.0": "lgpl-3.0",
    "AFL-3.0": "afl-3.0",
    "ECL-2.0": "ecl-2.0",
    "BSD-2-Clause": "bsd-2-clause",
    "BSD-3-Clause": "bsd-3-clause",
    "CC-BY-4.0": "cc-by-4.0",
    "CC-BY-SA-4.0": "cc-by-sa-4.0",
    "CC-BY-NC-4.0": "cc-by-nc-4.0",
    "CC0-1.0": "cc0-1.0",
    "Unlicense": "unlicense",
}


_STUDIO_FIELD_RENAMES: dict[str, str] = {
    "cover_image": "coverImage",
}

# Reserved fields that are controlled by create_repo method parameters.
# These MUST NOT be overridden via extra kwargs to avoid silent conflicts.
_RESERVED_EXTRA_FIELDS: frozenset[str] = frozenset({"Path", "Owner", "Name"})


class HubApi:
    """Unified client for ModelScope Hub operations.

    Provides a high-level interface for repository management, file
    operations, deployment, secret management and local caching. All
    repo-type-specific operations use a unified ``repo_type`` parameter
    following the OpenAPI-First design — there are no type-specific
    methods like ``create_model`` or ``get_dataset``.

    Internally the class composes :class:`OpenAPIClient`,
    :class:`LegacyClient`, :class:`DownloadManager`, :class:`UploadManager`
    and the cache helpers. HTTP clients are instantiated lazily, so
    ``HubApi()`` never fails just because no token is present.

    Parameters
    ----------
    config : HubConfig or None, optional
        Pre-built configuration. When omitted, the process-wide default
        from :func:`get_default_config` is used (which reads the
        ``MODELSCOPE_API_TOKEN`` env var and the local config file).
    endpoint : str or None, optional
        Override the API endpoint. Takes precedence over ``config.endpoint``.
        Defaults to ``https://modelscope.cn``.
    token : str or None, optional
        Override the API token. Takes precedence over ``config.token``.

    Examples
    --------
    >>> from modelscope_hub import HubApi
    >>> api = HubApi(token="ms-xxxxxxxx")
    >>> user = api.whoami()
    >>> user.username
    'alice'

    Create and manage repositories:

    >>> api.create_repo("alice/my-model", repo_type="model", visibility="private")
    >>> api.upload_file("alice/my-model", "model", "./weights.bin", "weights.bin")
    >>> path = api.download_file("alice/my-model", "model", "weights.bin")
    """

    def __init__(
        self,
        config: HubConfig | None = None,
        *,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> None:
        base = config or get_default_config()
        if config is None and (endpoint is not None or token is not None):
            from dataclasses import replace

            was_overridden = base._endpoint_overridden
            base = replace(base)
            # replace() re-runs __post_init__ which sees the inherited
            # endpoint string as "explicit" and sets _endpoint_overridden.
            # Restore the original state so resolve_endpoint_for_read works.
            base._endpoint_overridden = was_overridden
        self._config = base
        if endpoint is not None:
            self._config.endpoint = endpoint.rstrip("/")
            self._config._endpoint_overridden = True
        if token is not None:
            self._config.token = token

        self._openapi: OpenAPIClient | None = None
        self._legacy: LegacyClient | None = None
        self._downloader: DownloadManager | None = None
        self._uploader: UploadManager | None = None

    # ==================================================================
    # Lazy client accessors
    # ==================================================================
    @property
    def openapi(self) -> OpenAPIClient:
        """Lazily-constructed OpenAPI client."""
        if self._openapi is None:
            self._openapi = OpenAPIClient(self._config)
        return self._openapi

    @property
    def legacy(self) -> LegacyClient:
        """Lazily-constructed legacy ``/api/v1`` client."""
        if self._legacy is None:
            from .utils import build_user_agent

            self._legacy = LegacyClient(
                token=self._config.token,
                endpoint=self._config.endpoint,
                user_agent=build_user_agent(self._config.get_session_id()),
            )
        elif self._legacy.token != self._config.token and self._config.token:
            self._legacy.token = self._config.token
        return self._legacy

    @property
    def downloader(self) -> DownloadManager:
        """Lazily-constructed :class:`DownloadManager`."""
        if self._downloader is None:
            self._downloader = DownloadManager(self.legacy, self._config)
        return self._downloader

    @property
    def uploader(self) -> UploadManager:
        """Lazily-constructed :class:`UploadManager`.

        The OpenAPI client is injected so small files (≤ 5 MiB) flow through
        ``POST /files/upload`` instead of the legacy commit endpoint.
        """
        if self._uploader is None:
            self._uploader = UploadManager(
                self.legacy,
                self._config,
                self.openapi,
                create_repo_fn=self._create_repo_exist_ok,
            )
        return self._uploader

    # ==================================================================
    # Static helpers
    # ==================================================================
    @staticmethod
    def _parse_repo_id(repo_id: str) -> tuple[str, str]:
        """Split a canonical ``owner/name`` identifier into its two halves."""
        if not repo_id or "/" not in repo_id:
            raise InvalidParameter(f"repo_id {repo_id!r} should be in format of 'owner/name'.")
        owner, _, name = repo_id.partition("/")
        if not owner or not name:
            raise InvalidParameter(
                f"repo_id {repo_id!r} should be in format of 'owner/name': owner and name must both be non-empty."
            )
        return owner, name

    def _create_repo_exist_ok(self, repo_id: str, repo_type: str) -> None:
        """Auto-create the repo if it doesn't exist, silently ignore if it does."""
        try:
            self.create_repo(repo_id, repo_type)
        except HubError:
            pass

    @staticmethod
    def _normalize_repo_type(repo_type: RepoTypeLike) -> RepoType:
        """Coerce a ``str`` or :class:`RepoType` value to a :class:`RepoType`."""
        if isinstance(repo_type, RepoType):
            return repo_type
        try:
            return RepoType(str(repo_type).lower())
        except ValueError as exc:
            allowed = ", ".join(t.value for t in RepoType)
            raise InvalidParameter(f"Unknown repo_type {repo_type!r}. Expected one of: {allowed}.") from exc

    @staticmethod
    def _normalize_visibility(visibility: int | str | Visibility | None) -> int | None:
        """Normalise visibility input to its integer wire encoding."""
        if visibility is None:
            return None
        if isinstance(visibility, Visibility):
            return int(visibility)
        if isinstance(visibility, int):
            return visibility
        return int(Visibility.from_label(str(visibility)))

    _PAGED_ITEM_KEYS = (
        "items",
        "list",
        "data",
        "results",
        "models",
        "datasets",
        "skills",
        "servers",
        "mcp_server_list",
        "Models",
        "Datasets",
        "Skills",
        "Servers",
    )
    _PAGED_META_KEYS = frozenset(
        {
            "total_count",
            "total",
            "page_number",
            "page",
            "page_size",
            "size",
            "TotalCount",
            "Total",
            "PageNumber",
            "PageSize",
        }
    )

    @staticmethod
    def _extract_paged(payload: Any) -> tuple[list[Any], int, int, int]:
        """Decode a paginated OpenAPI response into ``(items, total, page, size)``.

        The ModelScope API returns item arrays under type-specific keys
        (``models``, ``datasets``, ``skills``, ``servers``). This method
        checks known keys first, then falls back to the first list-valued
        key that is not pagination metadata.
        """
        if isinstance(payload, list):
            return payload, len(payload), 1, len(payload)
        if not isinstance(payload, dict):
            return [], 0, 1, 0

        items: list[Any] = []
        for key in HubApi._PAGED_ITEM_KEYS:
            if isinstance(payload.get(key), list):
                items = payload[key]
                break
        else:
            for key, value in payload.items():
                if isinstance(value, list) and key not in HubApi._PAGED_META_KEYS:
                    items = value
                    break

        def _first(keys: tuple[str, ...], default: int) -> int:
            for k in keys:
                v = payload.get(k)
                if v is not None:
                    return int(v)
            return default

        total = _first(("total_count", "TotalCount", "total"), len(items))
        page = _first(("page_number", "PageNumber", "page"), 1)
        size = _first(("page_size", "PageSize", "size"), len(items))
        return items, total, page, size

    @staticmethod
    def _repo_info_from_payload(
        data: Mapping[str, Any] | None,
        repo_type: RepoType,
        *,
        owner_hint: str | None = None,
        name_hint: str | None = None,
    ) -> RepoInfo:
        """Build a :class:`RepoInfo` from an arbitrary API payload.

        The legacy and OpenAPI surfaces use different field-naming conventions
        (PascalCase vs snake_case). This helper normalises both into the
        SDK's canonical dataclass.
        """
        data = dict(data or {})
        # PascalCase → snake_case shims for legacy responses.
        normalised: dict[str, Any] = {}
        aliases = {
            "Id": "id",
            "Path": "owner",
            "Name": "name",
            "Owner": "owner",
            "Visibility": "visibility",
            "License": "license",
            "Description": "description",
            "Downloads": "downloads",
            "Likes": "likes",
            "CreatedAt": "created_at",
            "UpdatedAt": "last_modified",
            "LastModified": "last_modified",
            "last_modified": "last_modified",
            "updated_at": "last_modified",
            "Tags": "tags",
        }
        for key, value in data.items():
            normalised[aliases.get(key, key)] = value

        # The OpenAPI surface uses ``private`` bool for visibility.
        # gated is orthogonal and does not affect visibility mapping.
        if normalised.get("visibility") is None:
            private_flag = normalised.get("private")
            if isinstance(private_flag, bool):
                if private_flag:
                    normalised["visibility"] = Visibility.PRIVATE
                else:
                    normalised["visibility"] = Visibility.PUBLIC
            elif normalised.get("gated"):
                # Rule 4: visibility unknown + gated=True → imply PRIVATE
                normalised["visibility"] = Visibility.PRIVATE

        # The OpenAPI list endpoints return ``id`` as "owner/name".
        # Split it so the computed ``repo_id`` property works.
        id_val = normalised.get("id")
        if isinstance(id_val, str) and "/" in id_val:
            parts = id_val.split("/", 1)
            if not normalised.get("owner"):
                normalised["owner"] = parts[0]
            if not normalised.get("name"):
                normalised["name"] = parts[1]

        if not normalised.get("owner"):
            normalised["owner"] = owner_hint
        if not normalised.get("name"):
            normalised["name"] = name_hint
        normalised["repo_type"] = repo_type
        return RepoInfo.from_dict(normalised)

    # ==================================================================
    # Authentication
    # ==================================================================
    def get_cookies(
        self,
        access_token: str | None = None,
        *,
        cookies_required: bool = False,
    ) -> RequestsCookieJar | None:
        """Get cookies for authentication from token or local cache.

        Resolution order:
        1. Explicit ``access_token`` argument
        2. Token from config (explicit arg > env var > persisted cookie)
        3. Saved cookies from ``~/.modelscope/credentials/cookies``

        When a token is available (steps 1-2), a fresh
        :class:`~requests.cookies.RequestsCookieJar` with ``m_session_id``
        is built. Otherwise the locally cached cookies from a prior
        ``login()`` call are loaded.

        Parameters
        ----------
        access_token : str, optional
            Explicit token override.
        cookies_required : bool, optional
            When ``True``, raise :class:`AuthenticationError` if no
            credentials are available. Default is ``False``.

        Returns
        -------
        RequestsCookieJar or None
            Cookie jar for authentication, or ``None`` when no
            credentials are available and ``cookies_required`` is ``False``.

        Raises
        ------
        AuthenticationError
            When ``cookies_required`` is ``True`` and no credentials found.

        Examples
        --------
        >>> cookies = api.get_cookies()
        >>> cookies['m_session_id']
        'ms-xxxxxxxx'
        """
        token = access_token or self._config.token
        if token:
            domain = urlparse(self._config.endpoint).hostname or ""
            jar = RequestsCookieJar()
            jar.set("m_session_id", token, domain=domain, path="/")
            return jar

        cookies = self._config.load_cookies()
        if cookies is not None:
            return cookies

        if cookies_required:
            raise AuthenticationError(
                "No credentials found. "
                "Pass --token, call HubApi.login(), or set MODELSCOPE_API_TOKEN. "
                "Your token is available at https://modelscope.cn/my/myaccesstoken"
            )
        return None

    def login(self, token: str) -> UserInfo:
        """Authenticate and persist credentials locally.

        Calls ``POST /api/v1/login`` to obtain server-issued session cookies
        and a git access token, then saves them to
        ``~/.modelscope/credentials/`` (compatible with the old modelscope SDK).

        Parameters
        ----------
        token : str
            ModelScope API token. Must be non-empty after stripping.

        Returns
        -------
        UserInfo
            Profile of the authenticated user.

        Raises
        ------
        InvalidParameter
            When ``token`` is empty or whitespace-only.
        AuthenticationError
            When the server rejects the token. The bad token is cleared
            from local storage before re-raising.

        Examples
        --------
        >>> api = HubApi()
        >>> user = api.login("ms-xxxxxxxx")
        >>> user.username
        'alice'
        """
        if not token or not token.strip():
            raise InvalidParameter("token must be a non-empty string")

        token = token.strip()
        self._config.token = token
        self._config._logged_out = False
        self._openapi = None
        if self._legacy is not None:
            self._legacy.token = token

        try:
            data, cookies = self.legacy.login(token)
        except (AuthenticationError, HubError) as exc:
            self._config.clear_token()
            raise AuthenticationError(
                "Login failed: the provided token was rejected by the server.",
                status_code=getattr(exc, "status_code", None),
            ) from exc

        git_token = data.get("AccessToken", "")
        username = data.get("Username", "")
        email = data.get("Email", "")

        self._config.save_cookies(cookies)
        if git_token:
            self._config.save_git_token(git_token)
        if username:
            self._config.save_user_info(username, email or "")

        return self.whoami()

    def logout(self) -> None:
        """Clear the locally persisted token.

        Cached HTTP clients are reset so subsequent calls behave as if
        no credential was ever provided.

        Examples
        --------
        >>> api.logout()
        """
        self._config.clear_token()
        self._openapi = None
        if self._legacy is not None:
            self._legacy.token = None

    def whoami(self) -> UserInfo:
        """Return the profile for the currently authenticated user.

        Returns
        -------
        UserInfo
            Authenticated user profile (username, email, avatar, ...).

        Raises
        ------
        AuthenticationError
            When no token is configured or the token is invalid.

        Examples
        --------
        >>> from modelscope_hub import HubApi
        >>> api = HubApi(token="ms-xxxxxxxx")
        >>> user = api.whoami()
        >>> print(user.username, user.email)
        alice alice@example.com
        """
        payload = self.openapi.get_current_user()
        return UserInfo.from_dict(payload if isinstance(payload, dict) else {})

    # ==================================================================
    # Unified repo CRUD
    # ==================================================================
    def create_repo(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        *,
        visibility: int | str | Visibility | None = None,
        license: str | None = None,
        chinese_name: str | None = None,
        description: str | None = None,
        gated_mode: bool | None = None,
        **extra: Any,
    ) -> RepoInfo:
        """Create a new repository.

        Routing is decided by ``repo_type``:

        * ``studio`` / ``skill`` → OpenAPI ``POST /studios`` / ``POST /skills``
        * ``model`` / ``dataset`` → legacy ``POST /api/v1/{type}s``

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            One of ``"model"``, ``"dataset"``, ``"studio"``, ``"skill"``.
        visibility : int, str or Visibility, optional
            Visibility level. Accepts the integer wire encoding, a label
            (``"public"`` / ``"private"``) or a :class:`Visibility` value.
            Defaults to public.
        license : str, optional
            SPDX-style license identifier (e.g. ``"apache-2.0"``).
        chinese_name : str, optional
            Chinese display name shown on the Hub UI.
        description : str, optional
            Short description of the repository.
        gated_mode : bool, optional
            Enable gated (application-based download) mode for private repos.
            True = gated, False = normal private. Only effective when
            visibility is PRIVATE; ignored otherwise.
        **extra : Any
            Additional fields forwarded verbatim to the underlying client.

        Returns
        -------
        RepoInfo
            Metadata of the newly created repository.

        Raises
        ------
        InvalidParameter
            When ``repo_id`` does not have the ``owner/name`` shape.
        AuthenticationError
            When the token is missing or invalid.

        Examples
        --------
        Create a private model repository:

        >>> info = api.create_repo(
        ...     "alice/llama-7b-finetuned",
        ...     repo_type="model",
        ...     visibility="private",
        ...     license="apache-2.0",
        ...     description="A LoRA fine-tune of LLaMA-7B",
        ... )
        >>> info.repo_id
        'alice/llama-7b-finetuned'

        Create a private gated dataset:

        >>> api.create_repo("alice/my-data", "dataset", visibility="private", gated_mode=True)

        Create a public Studio space:

        >>> api.create_repo("alice/chat-demo", repo_type="studio", visibility="public")
        """
        rt = self._normalize_repo_type(repo_type)
        if rt not in _CREATABLE_TYPES:
            supported = ", ".join(sorted(t.value for t in _CREATABLE_TYPES))
            raise NotSupportedError(
                f"create_repo does not support repo_type={rt.value!r}. Supported types: {supported}."
            )
        owner, name = self._parse_repo_id(repo_id)
        vis = self._normalize_visibility(visibility)
        if license is not None:
            license = _LICENSE_DISPLAY_TO_SPDX.get(license, license)

        if rt in _OPENAPI_CREATE_TYPES:
            is_private = vis is not None and vis == int(Visibility.PRIVATE)
            if rt is RepoType.STUDIO:
                payload: dict[str, Any] = {
                    "owner": owner,
                    "repo_name": name,
                }
                if vis is not None:
                    payload["private"] = is_private
                if chinese_name is not None:
                    payload["display_name"] = chinese_name
            else:
                payload = {
                    "owner": owner,
                    "skill_name": name,
                }
                if vis is not None:
                    payload["private"] = is_private
                if chinese_name is not None:
                    payload["display_name"] = chinese_name
            if license is not None:
                payload["license"] = license
            if description is not None:
                payload["description"] = description
            for old_key, new_key in _STUDIO_FIELD_RENAMES.items():
                if old_key in extra:
                    extra[new_key] = extra.pop(old_key)
            payload.update(extra)
            data = self.openapi.create_studio(payload) if rt is RepoType.STUDIO else self.openapi.create_skill(payload)
            return self._repo_info_from_payload(data, rt, owner_hint=owner, name_hint=name)

        if rt is RepoType.DATASET:
            body: dict[str, Any] = {
                "Owner": owner,
                "Name": name,
                "Visibility": vis if vis is not None else int(Visibility.PUBLIC),
                "License": license or "Apache-2.0",
            }
        else:
            body = {
                "Path": owner,
                "Name": name,
                "Visibility": vis if vis is not None else int(Visibility.PUBLIC),
                "License": license or "Apache-2.0",
            }
        if chinese_name is not None:
            body["ChineseName"] = chinese_name
        if description is not None:
            body["Description"] = description

        # gated_mode → ProtectedMode wire field (1=gated, 2=off).
        # gated only effective with PRIVATE; when vis=None + gated=True,
        # implicitly set visibility to PRIVATE (user intent: gated repo).
        if gated_mode is not None:
            if vis is None:
                vis = int(Visibility.PRIVATE)
                body["Visibility"] = vis
                body["ProtectedMode"] = 1 if gated_mode else 2
            elif vis == int(Visibility.PRIVATE):
                body["ProtectedMode"] = 1 if gated_mode else 2
            else:
                logger.warning("gated_mode is only effective when visibility is PRIVATE, ignored.")

        # Blocklist filtering: only reject fields controlled by method params.
        filtered: dict[str, Any] = {}
        for k, v in extra.items():
            if k in _RESERVED_EXTRA_FIELDS:
                logger.warning("Reserved field %r in extra ignored (controlled by method params)", k)
                continue
            filtered[k] = v
        if "ProtectedMode" in filtered:
            pm = filtered["ProtectedMode"]
            if not isinstance(pm, int) or isinstance(pm, bool) or pm not in (1, 2):
                raise ValueError("ProtectedMode must be int 1 (gated) or 2 (off); use gated_mode=True/False instead")
        body.update(filtered)

        data = self.legacy.create_repo(repo_type=str(rt), body=body)
        return self._repo_info_from_payload(data, rt, owner_hint=owner, name_hint=name)

    def get_repo(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        *,
        revision: str | None = None,  # noqa: ARG002 - reserved for future use
    ) -> RepoInfo:
        """Fetch a repository's metadata via the OpenAPI surface.

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            One of ``"model"``, ``"dataset"``, ``"studio"``, ``"skill"``, ``"mcp"``.
        revision : str, optional
            Reserved for future use; currently ignored.

        Returns
        -------
        RepoInfo
            Repository metadata (id, owner, name, visibility, stats, ...).

        Raises
        ------
        NotExistError
            When the repository does not exist or is not visible to the caller.
        AuthenticationError
            When the request requires auth and the token is missing or invalid.

        Examples
        --------
        >>> info = api.get_repo("alice/llama-7b", repo_type="model")
        >>> info.visibility
        'public'
        >>> info.downloads
        1234
        """
        rt = self._normalize_repo_type(repo_type)
        owner, name = self._parse_repo_id(repo_id)

        if rt is RepoType.MODEL:
            try:
                data = self.openapi.get_model(owner, name)
            except NotExistError:
                data = self.legacy.get_repo_info(repo_id, str(rt))
        elif rt is RepoType.DATASET:
            try:
                data = self.openapi.get_dataset(owner, name)
            except NotExistError:
                logger.debug(
                    "Dataset %s/%s not found in OpenAPI, falling back to legacy API",
                    owner,
                    name,
                )
                data = self.legacy.get_repo_info(repo_id, str(rt))
        elif rt is RepoType.STUDIO:
            data = self.openapi.get_studio(owner, name)
        elif rt is RepoType.SKILL:
            data = self.openapi.get_skill(f"{owner}/{name}")
        elif rt is RepoType.MCP:
            data = self.openapi.get_mcp_server(f"{owner}/{name}")
        else:  # pragma: no cover - defensive
            raise NotSupportedError(f"get_repo not supported for {rt}")

        return self._repo_info_from_payload(data, rt, owner_hint=owner, name_hint=name)

    def list_repos(
        self,
        repo_type: RepoTypeLike,
        *,
        owner: str | None = None,
        search: str | None = None,
        sort: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        **filters: Any,
    ) -> PagedResult[RepoInfo]:
        """List repositories of the given type via OpenAPI.

        Parameters
        ----------
        repo_type : str or RepoType
            One of ``"model"``, ``"dataset"``, ``"skill"``, ``"mcp"``.
            ``"studio"`` raises :class:`NotSupportedError` (no list endpoint).
        owner : str, optional
            Restrict results to repositories owned by this user/org.
        search : str, optional
            Free-text search query.
        sort : str, optional
            Sort key understood by the upstream endpoint (e.g. ``"downloads"``).
        page_number : int, optional
            1-based page index. Default is 1.
        page_size : int, optional
            Items per page. Default is 10.
        **filters : Any
            Additional filter fields. ``None`` values are dropped.

        Returns
        -------
        PagedResult[RepoInfo]
            Paginated repository listing.

        Raises
        ------
        NotSupportedError
            When ``repo_type`` is ``"studio"`` (no list endpoint yet).

        Examples
        --------
        Browse public LLaMA models:

        >>> page = api.list_repos("model", search="llama", page_size=5)
        >>> page.total_count
        42
        >>> [r.repo_id for r in page.items]
        ['meta-llama/Llama-2-7b', ...]

        List datasets owned by an organisation:

        >>> api.list_repos("dataset", owner="my_org", page_number=2)
        """
        rt = self._normalize_repo_type(repo_type)
        clean_filters: dict[str, Any] = {k: v for k, v in filters.items() if v is not None}

        if rt is RepoType.MODEL:
            payload = self.openapi.list_models(
                search=search,
                owner=owner,
                sort=sort,
                page_number=page_number,
                page_size=page_size,
                filters=clean_filters or None,
            )
        elif rt is RepoType.DATASET:
            payload = self.openapi.list_datasets(
                search=search,
                owner=owner,
                sort=sort,
                page_number=page_number,
                page_size=page_size,
                filters=clean_filters or None,
            )
        elif rt is RepoType.SKILL:
            if owner:
                clean_filters.setdefault("owner", owner)
            payload = self.openapi.list_skills(
                search=search,
                page_number=page_number,
                page_size=page_size,
                filters=clean_filters or None,
            )
        elif rt is RepoType.MCP:
            payload = self.openapi.list_mcp_servers(
                search=search,
                page_number=page_number,
                page_size=page_size,
                filter=clean_filters or None,
            )
        elif rt is RepoType.STUDIO:
            raise NotSupportedError("Listing studios is not supported by the OpenAPI surface yet.")
        else:  # pragma: no cover - defensive
            raise NotSupportedError(f"list_repos not supported for {rt}")

        items, total, page, size = self._extract_paged(payload)
        # MCP response omits page_number/page_size — use requested values.
        if rt is RepoType.MCP:
            page = page_number
            size = page_size
        infos = [self._repo_info_from_payload(item, rt) for item in items]
        # Determine collection key for OpenAPI-aligned to_dict() output
        _COLLECTION_KEYS = {
            RepoType.MODEL: "models",
            RepoType.DATASET: "datasets",
            RepoType.SKILL: "skills",
            RepoType.MCP: "servers",
        }
        key = _COLLECTION_KEYS.get(rt, "items")
        return PagedResult(items=infos, total_count=total, page_number=page, page_size=size, collection_key=key)

    def delete_repo(self, repo_id: str, repo_type: RepoTypeLike) -> None:
        """Delete a repository.

        .. deprecated::
            Programmatic repository deletion is not currently supported by
            the Hub API for security reasons. This method will be restored
            in a future release once proper token-scoped authentication is
            available. To delete a repository now, use the web console at
            https://modelscope.cn.

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            Repository type (``"model"``, ``"dataset"``, etc.).
        """
        import warnings

        warnings.warn(
            "This function is deprecated due to security reasons, "
            "and will be recovered in future versions with proper token authentication. "
            "Please go to https://modelscope.cn to delete repositories via the web console.",
            DeprecationWarning,
            stacklevel=2,
        )
        rt = self._normalize_repo_type(repo_type)
        self._parse_repo_id(repo_id)
        self.legacy.delete_repo(repo_id=repo_id, repo_type=str(rt))

    def repo_exists(self, repo_id: str, repo_type: RepoTypeLike) -> bool:
        """Return ``True`` iff the repository exists and is visible to the caller.

        This is a thin wrapper around :meth:`get_repo` that converts a
        :class:`NotExistError` into a boolean.

        Examples
        --------
        >>> api.repo_exists("alice/my-model", "model")
        True
        """
        try:
            self.get_repo(repo_id, repo_type)
            return True
        except NotExistError:
            return False

    def resolve_endpoint_for_read(
        self,
        repo_id: str,
        *,
        repo_type: RepoTypeLike = "model",
        token: str | None = None,
    ) -> str:
        """Resolve the best endpoint for read operations (download, list, get).

        1. If the endpoint was explicitly configured (via constructor arg,
           ``MODELSCOPE_ENDPOINT``, or the deprecated ``MODELSCOPE_DOMAIN``),
           trust the user's configuration and return it directly (no probe).
        2. If ``MODELSCOPE_PREFER_AI_SITE=true``, check ``.ai`` first, then
           fall back to ``.cn``.
        3. Otherwise (default), check ``.cn`` first, then fall back to ``.ai``.

        Parameters
        ----------
        token : str, optional
            Explicit token for the probe requests.  Falls back to the
            token stored in this instance's config.

        Returns
        -------
        str
            The endpoint URL where the repo exists.

        Raises
        ------
        NotExistError
            If the repo is not found on any checked endpoint.
        """
        from .constants import (
            DEFAULT_ENDPOINT,
            DEFAULT_INTL_ENDPOINT,
            ENV_PREFER_AI_SITE,
            _env_bool,
        )

        if self._config._endpoint_overridden:
            return self._config.endpoint

        effective_token = token or self._config.token

        prefer_ai = _env_bool(ENV_PREFER_AI_SITE, False)
        primary = DEFAULT_INTL_ENDPOINT if prefer_ai else DEFAULT_ENDPOINT
        fallback = DEFAULT_ENDPOINT if prefer_ai else DEFAULT_INTL_ENDPOINT

        primary_probe = HubApi(endpoint=primary, token=effective_token)
        if primary_probe.repo_exists(repo_id, repo_type):
            return primary

        fallback_probe = HubApi(endpoint=fallback, token=effective_token)
        if fallback_probe.repo_exists(repo_id, repo_type):
            logger.warning(
                "Repo %s not found on %s, using %s instead.",
                repo_id,
                primary,
                fallback,
            )
            return fallback

        raise NotExistError(f"Repo {repo_id} not found on either {primary} or {fallback}")

    # ==================================================================
    # Files
    # ==================================================================
    def upload_file_to_openapi(self, file: str | Path | BinaryIO) -> str:
        """Upload a file (max 5 MiB) via OpenAPI and return the file ID.

        This is a generic upload not tied to any repository.  The returned
        ID can be used in subsequent API calls (e.g. ``skill_file`` when
        creating a skill).
        """
        data = self.openapi.upload_file(file=file)
        return data["id"]

    def upload_file(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        path_or_fileobj: str | Path | bytes | BinaryIO,
        path_in_repo: str,
        *,
        commit_message: str | None = None,
        commit_description: str | None = None,
        revision: str | None = None,
        buffer_size_mb: int = 16,
        disable_tqdm: bool = False,
    ) -> dict:
        """Upload a single file to a repository.

        LFS files upload/reuse their blob first, then commit an LFS pointer.
        Normal files are committed directly with inline base64 content.
        LFS mode is determined by file suffix and size threshold.

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            Repository type (``"model"``, ``"dataset"``, ...).
        path_or_fileobj : str, Path, bytes or BinaryIO
            Local path, raw bytes, or a binary file-like object.
        path_in_repo : str
            Destination path inside the repository.
        commit_message : str, optional
            Commit message. Defaults to ``"Upload file"``.
        commit_description : str, optional
            Extended commit description.
        revision : str, optional
            Branch to commit on. Defaults to ``"master"``.
        buffer_size_mb : int, optional
            Buffer size in MiB for reading file data. Default 16.
        disable_tqdm : bool, optional
            Disable progress bar. Default False.

        Returns
        -------
        dict
            Commit info from the server.

        Raises
        ------
        AuthenticationError
            When the token is missing or invalid.
        NotExistError
            When the target repository does not exist.

        Examples
        --------
        >>> api.upload_file(
        ...     "alice/llama-7b",
        ...     repo_type="model",
        ...     path_or_fileobj="./pytorch_model.bin",
        ...     path_in_repo="pytorch_model.bin",
        ...     commit_message="Add fine-tuned weights",
        ... )
        """
        rt = self._normalize_repo_type(repo_type)
        return self.uploader.upload_file(
            repo_id=repo_id,
            repo_type=str(rt),
            path_or_fileobj=path_or_fileobj,
            path_in_repo=path_in_repo,
            commit_message=commit_message or "Upload file",
            commit_description=commit_description,
            revision=revision or "master",
            buffer_size_mb=buffer_size_mb,
            disable_tqdm=disable_tqdm,
        )

    def upload_folder(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        folder_path: str | Path,
        *,
        path_in_repo: str = "",
        commit_message: str | None = None,
        commit_description: str | None = None,
        revision: str | None = None,
        allow_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        max_workers: int | None = None,
        use_cache: bool = True,
        disable_tqdm: bool = False,
        sync_remote_repo: bool = False,
    ) -> dict | list[dict] | None:
        """Upload an entire folder to a repository with resumable support.

        Files are walked recursively from ``folder_path`` and uploaded in
        parallel with adaptive batching, per-file retry, and ReAct progressive
        retry fallback.

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            Repository type.
        folder_path : str or Path
            Local directory whose contents will be uploaded.
        path_in_repo : str, optional
            Destination prefix inside the repository. Defaults to the repo root.
        commit_message : str, optional
            Commit message. Defaults to ``"Upload folder"``.
        commit_description : str, optional
            Extended commit description.
        revision : str, optional
            Branch to commit on. Defaults to ``"master"``.
        allow_patterns : list of str, optional
            If given, only files matching at least one pattern are uploaded.
        ignore_patterns : list of str, optional
            Files matching any pattern are skipped.
        max_workers : int, optional
            Concurrency for parallel uploads. Defaults to adaptive.
        use_cache : bool, optional
            Use ``.ms_upload_cache`` for resumable uploads. Default True.
        disable_tqdm : bool, optional
            Disable progress bars. Default False.
        sync_remote_repo : bool, optional
            If True, delete remote files that are not present locally after
            a successful upload (sync semantics). Default False.

        Returns
        -------
        None
            If all files were already committed (nothing to do).
        dict
            If only one batch was committed.
        list of dict
            If multiple batches were committed.

        Examples
        --------
        >>> api.upload_folder(
        ...     "alice/llama-7b",
        ...     repo_type="model",
        ...     folder_path="./checkpoint-1000",
        ...     ignore_patterns=["*.optim", "events.out.*"],
        ...     max_workers=8,
        ... )
        """
        rt = self._normalize_repo_type(repo_type)
        return self.uploader.upload_folder(
            repo_id=repo_id,
            repo_type=str(rt),
            folder_path=folder_path,
            path_in_repo=path_in_repo,
            commit_message=commit_message or "Upload folder",
            commit_description=commit_description,
            revision=revision or "master",
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            max_workers=max_workers,
            use_cache=use_cache,
            disable_tqdm=disable_tqdm,
            sync_remote_repo=sync_remote_repo,
        )

    def download_file(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        file_path: str,
        *,
        revision: str | None = None,
        cache_dir: str | Path | None = None,
        local_dir: str | Path | None = None,
        force: bool = False,
        expected_sha256: str | None = None,
        local_files_only: bool = False,
        user_agent: dict | str | None = None,
    ) -> Path:
        """Download a single file from a repository.

        The file is fetched into the local cache and a path pointing at the
        cached blob is returned. Subsequent calls reuse the cached copy
        unless ``force=True``.

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            Repository type.
        file_path : str
            Path of the file inside the repository.
        revision : str, optional
            Branch, tag or commit SHA. Defaults to ``"master"``.
        cache_dir : str or Path, optional
            Override the default cache directory.
        local_dir : str or Path, optional
            When set, download directly into this directory instead of cache.
        force : bool, optional
            Re-download even if a cached copy exists. Default is ``False``.
        expected_sha256 : str, optional
            When provided, verify downloaded file hash and use it for
            cache hit validation. On mismatch, re-download up to 3 times.
        local_files_only : bool, optional
            When ``True``, return the cached path without network access.
            Raises :class:`CacheNotFound` if the file is not cached.
        user_agent : dict, str or None, optional
            Custom user-agent info appended to the default UA string.

        Returns
        -------
        Path
            Absolute path to the downloaded file on disk.

        Raises
        ------
        NotExistError
            When the file or repository does not exist.

        Examples
        --------
        >>> path = api.download_file(
        ...     "alice/llama-7b",
        ...     repo_type="model",
        ...     file_path="config.json",
        ... )
        >>> path.read_text()[:30]
        '{\n  "architectures": [\n    "Ll'
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is RepoType.STUDIO:
            raise NotSupportedError(
                "File download is not supported for studio repositories. "
                "Studios are application containers without a file listing API. "
                f"To access studio source code, use: git clone https://modelscope.cn/studios/{repo_id}.git"
            )
        return self.downloader.download_file(
            repo_id=repo_id,
            repo_type=str(rt),
            file_path=file_path,
            revision=revision or "master",
            cache_dir=Path(cache_dir) if cache_dir else None,
            local_dir=Path(local_dir) if local_dir else None,
            force=force,
            expected_sha256=expected_sha256,
            local_files_only=local_files_only,
            user_agent=user_agent,
        )

    def download_repo(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        *,
        revision: str | None = None,
        cache_dir: str | Path | None = None,
        local_dir: str | Path | None = None,
        allow_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        max_workers: int = 4,
        local_files_only: bool = False,
        user_agent: dict | str | None = None,
        progress_callbacks: list[type[ProgressCallback]] | None = None,
    ) -> Path:
        """Download an entire repository snapshot.

        All files at the given ``revision`` are fetched into the local cache
        in parallel. The returned path is the snapshot root directory.

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            Repository type.
        revision : str, optional
            Branch, tag or commit SHA. Defaults to ``"master"``.
        cache_dir : str or Path, optional
            Override the default cache directory.
        local_dir : str or Path, optional
            When set, download directly into this directory instead of cache.
        allow_patterns : list of str, optional
            If given, only matching files are downloaded.
        ignore_patterns : list of str, optional
            Matching files are skipped.
        max_workers : int, optional
            Concurrency for parallel downloads. Default is 4.
        local_files_only : bool, optional
            When ``True``, return the cached snapshot path without network.
        user_agent : dict, str or None, optional
            Custom user-agent info for download headers.
        progress_callbacks : list of ProgressCallback subclasses, optional
            Callback *classes* (not instances); each is instantiated per file
            to report byte-level download progress.

        Returns
        -------
        Path
            Absolute path to the snapshot/local directory.

        Examples
        --------
        Download only the tokenizer assets of a model:

        >>> root = api.download_repo(
        ...     "alice/llama-7b",
        ...     repo_type="model",
        ...     allow_patterns=["tokenizer*", "*.json"],
        ...     max_workers=8,
        ... )
        >>> sorted(p.name for p in root.iterdir())
        ['config.json', 'tokenizer.json', 'tokenizer_config.json']
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is RepoType.STUDIO:
            raise NotSupportedError(
                "File download is not supported for studio repositories. "
                "Studios are application containers without a file listing API. "
                f"To access studio source code, use: git clone https://modelscope.cn/studios/{repo_id}.git"
            )
        return self.downloader.download_repo(
            repo_id=repo_id,
            repo_type=str(rt),
            revision=revision or "master",
            cache_dir=Path(cache_dir) if cache_dir else None,
            local_dir=Path(local_dir) if local_dir else None,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            max_workers=max_workers,
            local_files_only=local_files_only,
            user_agent=user_agent,
            progress_callbacks=progress_callbacks,
        )

    def list_repo_files(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        *,
        revision: str | None = None,
        recursive: bool = True,
    ) -> list[FileInfo]:
        """List files inside a repository (legacy — no OpenAPI equivalent).

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            Repository type.
        revision : str, optional
            Branch, tag or commit SHA. Defaults to ``"master"``.
        recursive : bool, optional
            Walk subdirectories recursively. Default is ``True``.

        Returns
        -------
        list of FileInfo
            File metadata entries (path, size, blob id, last modified, ...).

        Examples
        --------
        >>> files = api.list_repo_files("alice/llama-7b", "model")
        >>> [f.path for f in files][:3]
        ['README.md', 'config.json', 'pytorch_model.bin']
        """
        rt = self._normalize_repo_type(repo_type)
        raw = self.legacy.list_repo_files(
            repo_id=repo_id,
            repo_type=str(rt),
            revision=revision or "master",
            recursive=recursive,
        )
        files: list[FileInfo] = []
        for item in raw:
            normalised = {
                "path": item.get("Path") or item.get("path") or item.get("Name") or "",
                "size": int(item.get("Size") or item.get("size") or 0),
                "blob_id": item.get("BlobId") or item.get("blob_id") or item.get("Sha256"),
                "sha256": item.get("Sha256") or item.get("sha256"),
                "type": item.get("Type") or item.get("type") or "blob",
                "last_modified": item.get("CommittedDate") or item.get("last_modified"),
                "lfs": item.get("Lfs") or item.get("lfs"),
            }
            files.append(FileInfo.from_dict(normalised))
        return files

    def delete_files(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        file_paths: Iterable[str],
        *,
        commit_message: str | None = None,
        revision: str | None = None,
    ) -> dict:
        """Delete one or more files from a repository.

        .. note::
           File deletion is restricted by the server to cookie-based session
           auth (interactive login). API tokens (``ms-...``) may receive a 401
           "token no longer supports deletion operations" error.

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            Repository type.
        file_paths : iterable of str
            Paths of files to remove. Empty entries are ignored.
        commit_message : str, optional
            Unused (kept for API compatibility).
        revision : str, optional
            Branch to delete from. Defaults to ``"master"``.

        Returns
        -------
        dict
            Summary with ``deleted_files`` and ``failed_files`` lists.

        Raises
        ------
        InvalidParameter
            When ``file_paths`` resolves to an empty list.

        Examples
        --------
        >>> api.delete_files(
        ...     "alice/llama-7b",
        ...     "model",
        ...     ["old_weights.bin", "deprecated/config.json"],
        ... )
        """
        rt = self._normalize_repo_type(repo_type)
        paths = [p for p in file_paths if p]
        if not paths:
            raise InvalidParameter("file_paths must contain at least one non-empty path.")

        deleted, failed = [], []
        for p in paths:
            try:
                self.legacy.delete_file(
                    repo_id=repo_id,
                    repo_type=str(rt),
                    file_path=p,
                    revision=revision or "master",
                )
                deleted.append(p)
            except (AuthenticationError, NetworkError) as exc:
                failed.append(p)
                raise
            except Exception:
                failed.append(p)

        return {"deleted_files": deleted, "failed_files": failed, "total_files": len(paths)}

    # ==================================================================
    # Versioning
    # ==================================================================
    def list_repo_revisions(self, repo_id: str, repo_type: RepoTypeLike) -> list[dict]:
        """Return branches and tags of a repository (legacy).

        Examples
        --------
        >>> revs = api.list_repo_revisions("alice/llama-7b", "model")
        >>> [r["name"] for r in revs]
        ['master', 'v1.0', 'experimental']
        """
        rt = self._normalize_repo_type(repo_type)
        return self.legacy.list_revisions(repo_id=repo_id, repo_type=str(rt))

    def create_repo_tag(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        tag: str,
        *,
        revision: str | None = None,
    ) -> dict:
        """Create a tag pointing at ``revision`` (defaults to ``master``).

        Examples
        --------
        >>> api.create_repo_tag("alice/llama-7b", "model", "v1.0")
        """
        rt = self._normalize_repo_type(repo_type)
        return self.legacy.create_tag(
            repo_id=repo_id,
            repo_type=str(rt),
            tag=tag,
            revision=revision or "master",
        )

    # ==================================================================
    # Lifecycle (Studio / MCP)
    # ==================================================================
    def deploy_repo(
        self,
        repo_id: str,
        repo_type: RepoTypeLike = RepoType.STUDIO,
        *,
        payload: Mapping[str, Any] | None = None,
    ) -> dict:
        """Deploy a Studio space or an MCP server.

        Parameters
        ----------
        repo_id : str
            For Studios, an ``owner/name`` pair. For MCP servers, the
            server identifier accepted by the OpenAPI surface.
        repo_type : str or RepoType, optional
            ``"studio"`` (default) or ``"mcp"``.
        payload : Mapping, optional
            Deployment configuration forwarded verbatim to the backend
            (hardware tier, env vars, ...).

        Returns
        -------
        dict
            Deployment response payload (deployment id, status URL, ...).

        Raises
        ------
        NotSupportedError
            When ``repo_type`` is neither ``"studio"`` nor ``"mcp"``.

        Examples
        --------
        Deploy a Studio space on a GPU instance:

        >>> api.deploy_repo(
        ...     "alice/chat-demo",
        ...     repo_type="studio",
        ...     payload={"instance_type": "GPU-A10", "min_replicas": 1},
        ... )
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is RepoType.STUDIO:
            owner, name = self._parse_repo_id(repo_id)
            return self.openapi.deploy_studio(owner, name, payload)
        if rt is RepoType.MCP:
            return self.openapi.deploy_mcp_server(repo_id, payload)
        raise NotSupportedError(f"deploy_repo is not supported for repo_type={rt.value!r}.")

    def stop_repo(
        self,
        repo_id: str,
        repo_type: RepoTypeLike = RepoType.STUDIO,
    ) -> dict:
        """Stop a running Studio or undeploy an MCP server.

        Examples
        --------
        >>> api.stop_repo("alice/chat-demo", repo_type="studio")
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is RepoType.STUDIO:
            owner, name = self._parse_repo_id(repo_id)
            return self.openapi.stop_studio(owner, name)
        if rt is RepoType.MCP:
            return self.openapi.undeploy_mcp_server(repo_id)
        raise NotSupportedError(f"stop_repo is not supported for repo_type={rt.value!r}.")

    def get_repo_logs(
        self,
        repo_id: str,
        repo_type: RepoTypeLike = RepoType.STUDIO,
        *,
        log_type: str = "run",
        page_num: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        start_timestamp: int | None = None,
        end_timestamp: int | None = None,
    ) -> dict:
        """Fetch paginated runtime/build logs for a Studio space.

        Parameters
        ----------
        repo_id : str
            Studio identifier in ``owner/name`` form.
        repo_type : str or RepoType, optional
            Must be ``"studio"``. Defaults to :class:`RepoType.STUDIO`.
        log_type : str, optional
            Either ``"run"`` (default) or ``"build"``.
        page_num : int, optional
            1-based page index. Default is 1.
        page_size : int, optional
            Lines per page. Default is 20.
        keyword : str, optional
            Filter logs containing this substring.
        start_timestamp, end_timestamp : int, optional
            Unix timestamps (seconds) bounding the log window.

        Returns
        -------
        dict
            Paginated log payload.

        Raises
        ------
        NotSupportedError
            When ``repo_type`` is not ``"studio"``.

        Examples
        --------
        >>> logs = api.get_repo_logs(
        ...     "alice/chat-demo",
        ...     log_type="run",
        ...     keyword="ERROR",
        ...     page_size=50,
        ... )
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is not RepoType.STUDIO:
            raise NotSupportedError(f"get_repo_logs is currently only supported for studio (got {rt.value!r}).")
        owner, name = self._parse_repo_id(repo_id)
        return self.openapi.get_studio_logs(
            owner,
            name,
            log_type,
            page_num=page_num,
            page_size=page_size,
            keyword=keyword,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )

    def update_repo_settings(
        self,
        repo_id: str,
        repo_type: RepoTypeLike,
        **settings: Any,
    ) -> dict:
        """Update repo settings (Studio or Skill).

        Parameters
        ----------
        repo_id : str
            Canonical ``owner/name`` identifier.
        repo_type : str or RepoType
            Either ``"studio"`` or ``"skill"``.
        **settings : Any
            Setting key/value pairs forwarded to the backend.

        Returns
        -------
        dict
            Updated settings payload.

        Raises
        ------
        NotSupportedError
            When ``repo_type`` is neither studio nor skill.

        Examples
        --------
        >>> api.update_repo_settings(
        ...     "alice/chat-demo",
        ...     repo_type="studio",
        ...     visibility="public",
        ...     hardware="GPU-A10",
        ... )
        """
        rt = self._normalize_repo_type(repo_type)
        owner, name = self._parse_repo_id(repo_id)
        for old_key, new_key in _STUDIO_FIELD_RENAMES.items():
            if old_key in settings:
                settings[new_key] = settings.pop(old_key)
        if rt is RepoType.STUDIO:
            return self.openapi.update_studio_settings(owner, name, settings)
        if rt is RepoType.SKILL:
            return self.openapi.update_skill_settings(owner, name, settings)
        raise NotSupportedError(f"update_repo_settings is not supported for repo_type={rt.value!r}.")

    # ==================================================================
    # Secrets
    # ==================================================================
    def list_secrets(self, repo_id: str, repo_type: RepoTypeLike = RepoType.STUDIO) -> list[dict]:
        """List secrets attached to a Studio.

        Examples
        --------
        >>> api.list_secrets("alice/chat-demo")
        [{'key': 'OPENAI_API_KEY', 'updated_at': 1712345678}, ...]
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is not RepoType.STUDIO:
            raise NotSupportedError(f"Secret management is only supported for studio (got {rt.value!r}).")
        owner, name = self._parse_repo_id(repo_id)
        data = self.openapi.list_studio_secrets(owner, name)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("items", "secrets", "list"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    def add_secret(
        self,
        repo_id: str,
        key: str,
        value: str,
        repo_type: RepoTypeLike = RepoType.STUDIO,
    ) -> dict:
        """Add a new secret to a Studio.

        Examples
        --------
        >>> api.add_secret("alice/chat-demo", "OPENAI_API_KEY", "sk-...")
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is not RepoType.STUDIO:
            raise NotSupportedError("Only studio secrets are supported.")
        owner, name = self._parse_repo_id(repo_id)
        return self.openapi.add_studio_secret(owner, name, key, value)

    def update_secret(
        self,
        repo_id: str,
        key: str,
        value: str,
        repo_type: RepoTypeLike = RepoType.STUDIO,
    ) -> dict:
        """Update an existing secret value.

        Examples
        --------
        >>> api.update_secret("alice/chat-demo", "OPENAI_API_KEY", "sk-new-...")
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is not RepoType.STUDIO:
            raise NotSupportedError("Only studio secrets are supported.")
        owner, name = self._parse_repo_id(repo_id)
        return self.openapi.update_studio_secret(owner, name, key, value)

    def delete_secret(
        self,
        repo_id: str,
        key: str,
        repo_type: RepoTypeLike = RepoType.STUDIO,
    ) -> dict:
        """Delete a secret from a Studio.

        Examples
        --------
        >>> api.delete_secret("alice/chat-demo", "OPENAI_API_KEY")
        """
        rt = self._normalize_repo_type(repo_type)
        if rt is not RepoType.STUDIO:
            raise NotSupportedError("Only studio secrets are supported.")
        owner, name = self._parse_repo_id(repo_id)
        return self.openapi.delete_studio_secret(owner, name, key)

    # ==================================================================
    # MCP convenience wrappers
    # ==================================================================
    def list_mcp_servers(
        self,
        *,
        search: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        **extra: Any,
    ) -> PagedResult[dict]:
        """List MCP servers via the OpenAPI surface.

        Parameters
        ----------
        search : str, optional
            Free-text search query.
        page_number : int, optional
            1-based page index. Default is 1.
        page_size : int, optional
            Items per page. Default is 10.
        **extra : Any
            Additional filter fields. ``None`` values are dropped.

        Returns
        -------
        PagedResult[dict]
            Paginated MCP server listing.

        Examples
        --------
        >>> page = api.list_mcp_servers(search="weather", page_size=5)
        >>> page.total_count
        12
        """
        payload = self.openapi.list_mcp_servers(
            search=search,
            page_number=page_number,
            page_size=page_size,
            extra={k: v for k, v in extra.items() if v is not None} or None,
        )
        items, total, page, size = self._extract_paged(payload)
        return PagedResult(items=list(items), total_count=total, page_number=page, page_size=size)

    def get_mcp_server(
        self,
        server_id: str,
        *,
        get_operational_url: bool | None = None,
    ) -> dict:
        """Fetch a single MCP server's metadata.

        Parameters
        ----------
        server_id : str
            MCP server identifier.
        get_operational_url : bool, optional
            When ``True``, the response includes the live runtime URL.

        Returns
        -------
        dict
            MCP server metadata.

        Examples
        --------
        >>> info = api.get_mcp_server("alice/weather-mcp", get_operational_url=True)
        >>> info["operational_url"]
        'https://...'
        """
        return self.openapi.get_mcp_server(server_id, get_operational_url=get_operational_url)

    def deploy_mcp_server(self, server_id: str, *, payload: Mapping[str, Any] | None = None) -> dict:
        """Deploy or redeploy an MCP server.

        Examples
        --------
        >>> api.deploy_mcp_server("alice/weather-mcp", payload={"region": "cn-hangzhou"})
        """
        return self.openapi.deploy_mcp_server(server_id, payload)

    def undeploy_mcp_server(self, server_id: str) -> dict:
        """Undeploy a running MCP server.

        Examples
        --------
        >>> api.undeploy_mcp_server("alice/weather-mcp")
        """
        return self.openapi.undeploy_mcp_server(server_id)

    # ==================================================================
    # Cache
    # ==================================================================
    def verify_cache(
        self,
        repo_id: str,
        repo_type: RepoTypeLike = "model",
        *,
        revision: str | None = None,
        cache_dir: str | Path | None = None,
        local_dir: str | Path | None = None,
    ) -> CacheVerification:
        """Verify local repository files against SHA-256 checksums from the Hub."""
        if cache_dir is not None and local_dir is not None:
            raise InvalidParameter("cache_dir and local_dir are mutually exclusive")
        rt = self._normalize_repo_type(repo_type)
        _, resolved_revision = _resolve_verification_root(
            repo_id,
            str(rt),
            revision=revision,
            cache_dir=cache_dir,
            local_dir=local_dir,
        )
        files = self.list_repo_files(repo_id, rt, revision=resolved_revision, recursive=True)
        expected = {file.path: file.sha256 for file in files if not file.is_dir and file.path}
        return _verify_cache(
            repo_id,
            str(rt),
            expected,
            revision=resolved_revision,
            cache_dir=Path(cache_dir) if cache_dir else None,
            local_dir=Path(local_dir) if local_dir else None,
        )

    def scan_cache(self, cache_dir: str | Path | None = None) -> CacheInfo:
        """Inspect the local cache directory.

        Parameters
        ----------
        cache_dir : str or Path, optional
            Override the default cache root.

        Returns
        -------
        CacheInfo
            Aggregated cache stats (total bytes, repo entries, ...).

        Examples
        --------
        >>> info = api.scan_cache()
        >>> info.size_on_disk
        12345678
        >>> [r.repo_id for r in info.repos][:3]
        ['alice/llama-7b', 'bob/imagenet', 'carol/whisper-base']
        """
        return _scan_cache(Path(cache_dir) if cache_dir else None)

    def clear_cache(
        self,
        *,
        cache_dir: str | Path | None = None,
        repo_type: RepoTypeLike | None = None,
        repo_id: str | None = None,
    ) -> int:
        """Remove cached data and return the number of bytes freed.

        Parameters
        ----------
        cache_dir : str or Path, optional
            Override the default cache root.
        repo_type : str or RepoType, optional
            Restrict deletion to a single repository type.
        repo_id : str, optional
            Restrict deletion to a single repository id.

        Returns
        -------
        int
            Number of bytes reclaimed from disk.

        Examples
        --------
        Wipe the cache for a single model:

        >>> api.clear_cache(repo_type="model", repo_id="alice/llama-7b")
        4823412

        Wipe everything:

        >>> api.clear_cache()
        """
        rt_value: str | None = None
        if repo_type is not None:
            rt_value = str(self._normalize_repo_type(repo_type))
        return _clear_cache(
            cache_dir=Path(cache_dir) if cache_dir else None,
            repo_type=rt_value,
            repo_id=repo_id,
        )
