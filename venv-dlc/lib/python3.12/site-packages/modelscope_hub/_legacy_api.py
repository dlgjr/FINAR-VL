"""Internal client for ``/api/v1/`` endpoints not covered by the OpenAPI spec.

This module is **private** — external callers should interact through the
public :class:`~modelscope_hub.api.HubApi` facade.

Auth strategy
-------------
The legacy API authenticates via a session cookie (``m_session_id``) rather
than the ``Authorization: Bearer`` header used by the OpenAPI surface. On
first use the client sets ``m_session_id = <access_token>`` on the
``requests.Session`` cookie jar — no round-trip to ``/api/v1/login`` is
needed for API calls.
"""

from __future__ import annotations

import uuid
from typing import Any, BinaryIO, IO, Union
from urllib.parse import quote_plus, urlparse

import requests
from requests.adapters import HTTPAdapter, Retry

from .constants import (
    API_CONNECT_TIMEOUT,
    API_MAX_RETRIES,
    API_TIMEOUT,
    LEGACY_API_PREFIX,
    RepoType,
    UPLOAD_BLOB_CONNECT_TIMEOUT,
    UPLOAD_BLOB_READ_TIMEOUT,
    UPLOAD_RETRY_ALLOWED_METHODS,
)
from .errors import InvalidParameter, NetworkError, RequestTimeoutError, ServerError, raise_for_status
from .utils.logger import get_logger

logger = get_logger("legacy_api")

# ---------------------------------------------------------------------------
# Repo-type routing table: maps RepoType → URL path segment (plural)
# ---------------------------------------------------------------------------
_REPO_TYPE_SEGMENT: dict[str, str] = {
    RepoType.MODEL: "models",
    RepoType.DATASET: "datasets",
    RepoType.STUDIO: "studios",
    RepoType.SKILL: "skills",
    RepoType.MCP: "mcps",
}

# For /api/v1/repos/ style endpoints, all use "{type}s" pattern
_REPOS_SEGMENT: dict[str, str] = {
    RepoType.MODEL: "models",
    RepoType.DATASET: "datasets",
    RepoType.STUDIO: "studios",
    RepoType.SKILL: "skills",
    RepoType.MCP: "mcps",
}


def _resolve_segment(repo_type: str) -> str:
    """Return the URL path segment for the given repo_type."""
    return _REPO_TYPE_SEGMENT.get(repo_type, f"{repo_type}s")


class LegacyClient:
    """Internal client for /api/v1/ endpoints not covered by OpenAPI.

    All network IO goes through :meth:`_request`, which handles auth headers,
    retries, and structured error raising.
    """

    def __init__(
        self,
        token: str | None,
        endpoint: str,
        timeout: int = API_TIMEOUT,
        max_retries: int = API_MAX_RETRIES,
        user_agent: str | None = None,
    ) -> None:
        self._token = token
        self._endpoint = endpoint.rstrip("/")
        self._timeout: int | tuple[int, int] = (API_CONNECT_TIMEOUT, timeout)
        self._session_authenticated = False

        self._session = requests.Session()
        if user_agent:
            self._session.headers["User-Agent"] = user_agent
        retry = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=UPLOAD_RETRY_ALLOWED_METHODS,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def token(self) -> str | None:
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        self._token = value
        self._session_authenticated = False
        self._session.cookies.clear()

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------
    def _build_url(self, path: str) -> str:
        """Construct full URL from a path relative to the legacy API prefix."""
        return f"{self._endpoint}{LEGACY_API_PREFIX}/{path.lstrip('/')}"

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Request-ID": uuid.uuid4().hex,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra:
            headers.update(extra)
        return headers

    def _ensure_session_auth(self) -> None:
        """Set the ``m_session_id`` cookie on the session for legacy API auth.

        Both cookie and Bearer header are sent: older endpoints rely on
        the ``m_session_id`` cookie, while newer endpoints accept the
        ``Authorization: Bearer`` header. Sending both is harmless and
        maximises compatibility.
        """
        if self._session_authenticated or not self._token:
            return
        domain = urlparse(self._endpoint).hostname or ""
        self._session.cookies.set("m_session_id", self._token, domain=domain, path="/")
        self._session_authenticated = True
        logger.debug("Legacy session cookie set for domain=%s", domain)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        stream: bool = False,
    ) -> requests.Response:
        """Unified request dispatcher with auth, retry, and error handling."""
        self._ensure_session_auth()
        url = self._build_url(path)
        merged_headers = self._headers(headers)
        # Remove Content-Type for non-json payloads so requests can set
        # the correct boundary for multipart or the right encoding for data.
        if (data is not None or files is not None) and json_body is None:
            merged_headers.pop("Content-Type", None)

        logger.debug("%s %s", method, url)
        try:
            resp = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                data=data,
                files=files,
                headers=merged_headers,
                timeout=timeout or self._timeout,
                stream=stream,
            )
        except requests.exceptions.RetryError as exc:
            raise ServerError(f"Max retries exceeded: {exc}") from exc
        except requests.ConnectionError as exc:
            raise NetworkError(f"Connection failed: {exc}") from exc
        except requests.Timeout as exc:
            raise RequestTimeoutError(f"Request timed out: {exc}") from exc

        logger.debug("%s %s -> %s", method, url, resp.status_code)
        if resp.status_code >= 400:
            logger.debug(
                "Request failed: %s %s params=%s status=%s body=%s",
                method,
                url,
                params,
                resp.status_code,
                resp.text[:500] if resp.text else "",
            )
        raise_for_status(resp)
        return resp

    def _json_data(self, resp: requests.Response) -> Any:
        """Extract the 'Data' field from a standard legacy API JSON response."""
        body = resp.json()
        return body.get("Data", body)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    def login(self, access_token: str) -> tuple[dict, "requests.cookies.RequestsCookieJar"]:
        """Authenticate via access token and return (user_data, cookies).

        POST /api/v1/login

        Performs a full login round-trip that returns a git token and
        server-issued session cookies. For routine API access, the
        ``m_session_id`` cookie set by :meth:`_ensure_session_auth` is
        sufficient — this method is only needed when the caller wants the
        git token or the full cookie set from the server.
        """
        self._token = access_token
        self._session_authenticated = False
        self._session.cookies.clear()
        self._ensure_session_auth()
        resp = self._request("POST", "login", json_body={"AccessToken": access_token})
        return self._json_data(resp), resp.cookies

    # ------------------------------------------------------------------
    # Repo CRUD (model / dataset)
    # ------------------------------------------------------------------
    def create_repo(self, repo_type: str, body: dict[str, Any]) -> dict:
        """POST /api/v1/{type}s — create a new repository.

        ``body`` is the fully-constructed request payload (PascalCase keys).

        The dataset endpoint requires multipart form data (matching the
        upstream server implementation), while model uses JSON.
        """
        segment = _resolve_segment(repo_type)
        if repo_type in (RepoType.DATASET, "dataset"):
            files = {k: (None, str(v)) for k, v in body.items() if v is not None}
            resp = self._request("POST", segment, files=files)
        else:
            resp = self._request("POST", segment, json_body=body)
        return self._json_data(resp)

    def get_repo_info(self, repo_id: str, repo_type: str) -> dict:
        """GET /api/v1/{type}s/{repo_id} — fetch repository metadata.

        Uses cookie-based session auth which supports private repositories
        (unlike the OpenAPI Bearer-only endpoint).
        """
        segment = _resolve_segment(repo_type)
        resp = self._request("GET", f"{segment}/{repo_id}")
        return self._json_data(resp)

    def list_datasets(
        self,
        *,
        owner: str | None = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> dict:
        """GET /api/v1/datasets — list datasets with full private visibility.

        The legacy endpoint returns ALL datasets for the authenticated user
        (including private ones that the OpenAPI search index may miss).
        """
        params: dict[str, Any] = {
            "PageNumber": page_number,
            "PageSize": page_size,
        }
        if owner:
            params["owner"] = owner
        try:
            resp = self._request("GET", "datasets", params=params)
        except InvalidParameter as exc:
            if "fromIndex" in str(exc) and "toIndex" in str(exc):
                return {
                    "items": [],
                    "total_count": 0,
                    "page_number": page_number,
                    "page_size": page_size,
                }
            raise
        body = resp.json()
        return {
            "items": body.get("Data") or [],
            "total_count": body.get("TotalCount") or 0,
            "page_number": body.get("PageNumber") or page_number,
            "page_size": body.get("PageSize") or page_size,
        }

    def delete_repo(self, repo_id: str, repo_type: str) -> None:
        """Delete a repository.

        DELETE /api/v1/models/{owner}/{name}
        DELETE /api/v1/datasets/{dataset_id}
        """
        segment = _resolve_segment(repo_type)
        self._request("DELETE", f"{segment}/{repo_id}")

    # ------------------------------------------------------------------
    # File Tree
    # ------------------------------------------------------------------
    def list_repo_files(
        self,
        repo_id: str,
        repo_type: str,
        revision: str = "master",
        recursive: bool = True,
        root: str | None = None,
    ) -> list[dict]:
        """List files in a repository.

        Models/studios/etc: GET /api/v1/{type}s/{repo_id}/repo/files
        Datasets: GET /api/v1/datasets/{repo_id}/repo/tree
        """
        segment = _resolve_segment(repo_type)
        params: dict[str, Any] = {
            "Revision": revision,
            "Recursive": str(recursive),
        }
        if root:
            params["Root"] = root

        suffix = "repo/tree" if repo_type in (RepoType.DATASET, "dataset", "datasets") else "repo/files"
        resp = self._request("GET", f"{segment}/{repo_id}/{suffix}", params=params)
        data = self._json_data(resp)
        if isinstance(data, list):
            return data
        # Sometimes wrapped: {"Data": {"Files": [...]}}
        if isinstance(data, dict):
            return data.get("Files", data.get("files", []))
        return []

    def list_dataset_files_paginated(
        self,
        repo_id: str,
        revision: str = "master",
        page_size: int = 200,
        root_path: str = "/",
    ) -> list[dict]:
        """List files in a dataset repo using pagination.

        Datasets can have millions of files, so this method pages through
        ``GET /api/v1/datasets/{repo_id}/repo/tree`` with
        ``PageNumber``/``PageSize`` params.
        """
        all_files: list[dict] = []
        page_number = 1
        while True:
            params: dict[str, Any] = {
                "Revision": revision,
                "Recursive": "True",
                "PageNumber": page_number,
                "PageSize": page_size,
            }
            if root_path and root_path != "/":
                params["Root"] = root_path
            resp = self._request(
                "GET",
                f"datasets/{repo_id}/repo/tree",
                params=params,
            )
            data = self._json_data(resp)
            if isinstance(data, list):
                files = data
            elif isinstance(data, dict):
                files = data.get("Files", data.get("files", []))
            else:
                files = []

            all_files.extend(files)
            if len(files) < page_size:
                break
            page_number += 1
        return all_files

    # ------------------------------------------------------------------
    # Revisions
    # ------------------------------------------------------------------
    def list_revisions(self, repo_id: str, repo_type: str) -> list[dict]:
        """List branches and tags of a repository.

        GET /api/v1/{type}s/{repo_id}/revisions
        """
        segment = _resolve_segment(repo_type)
        resp = self._request("GET", f"{segment}/{repo_id}/revisions")
        data = self._json_data(resp)
        if isinstance(data, dict):
            revision_map = data.get("RevisionMap") or {}
            tags = revision_map.get("Tags") or []
            branches = revision_map.get("Branches") or []
            return tags + branches
        return data if isinstance(data, list) else []

    def list_revisions_detail(
        self,
        repo_id: str,
        repo_type: str,
        *,
        end_time: int | None = None,
    ) -> tuple[list[dict], list[dict]]:
        """List branches and tags as separate lists.

        GET /api/v1/{type}s/{repo_id}/revisions[?EndTime=...]

        Returns ``(branches, tags)`` where each element is a list of dicts
        with at least ``Revision`` and ``CreatedAt`` keys.
        """
        segment = _resolve_segment(repo_type)
        params: dict[str, Any] = {}
        if end_time is not None:
            params["EndTime"] = end_time
        resp = self._request(
            "GET", f"{segment}/{repo_id}/revisions", params=params or None,
        )
        data = self._json_data(resp)
        if isinstance(data, dict):
            revision_map = data.get("RevisionMap") or {}
            return (
                revision_map.get("Branches") or [],
                revision_map.get("Tags") or [],
            )
        return [], []

    def create_tag(
        self,
        repo_id: str,
        repo_type: str,
        tag: str,
        revision: str,
    ) -> dict:
        """Create a tag on a repository.

        POST /api/v1/{type}s/{repo_id}/repo/tag
        """
        segment = _resolve_segment(repo_type)
        body = {"TagName": tag, "Ref": revision}
        resp = self._request("POST", f"{segment}/{repo_id}/repo/tag", json_body=body)
        return self._json_data(resp)

    # ------------------------------------------------------------------
    # File deletion
    # ------------------------------------------------------------------
    def delete_file(
        self,
        repo_id: str,
        repo_type: str,
        file_path: str,
        revision: str = "master",
    ) -> dict:
        """Delete a single file from the repository.

        DELETE /api/v1/{type}s/{owner}/{name}/file?FilePath=...&Revision=...
        (for models)
        DELETE /api/v1/datasets/{owner}/{name}/repo?FilePath=...
        (for datasets)
        """
        segment = _resolve_segment(repo_type)
        if repo_type == RepoType.DATASET:
            resp = self._request(
                "DELETE",
                f"{segment}/{repo_id}/repo",
                params={"FilePath": file_path},
            )
        else:
            resp = self._request(
                "DELETE",
                f"{segment}/{repo_id}/file",
                params={"FilePath": file_path, "Revision": revision},
            )
        return self._json_data(resp)

    # ------------------------------------------------------------------
    # Git Commits
    # ------------------------------------------------------------------
    def create_commit(
        self,
        repo_id: str,
        repo_type: str,
        operations: list[dict],
        commit_message: str,
        revision: str = "master",
    ) -> dict:
        """Create a Git commit with file operations.

        POST /api/v1/repos/{type}s/{repo_id}/commit/{revision}

        Each operation should be a dict with keys:
        - action: "create" | "update" | "delete"
        - path: path in repo
        - type: "normal" | "lfs"
        - size: file size in bytes
        - sha256: hex digest (empty string for normal files)
        - content: base64 content (for normal files)
        - encoding: "base64" (for normal files)
        """
        segment = _resolve_segment(repo_type)
        payload = {
            "commit_message": commit_message,
            "actions": operations,
        }
        resp = self._request(
            "POST",
            f"repos/{segment}/{repo_id}/commit/{revision}",
            json_body=payload,
        )
        return self._json_data(resp)

    # ------------------------------------------------------------------
    # Blob Upload (LFS)
    # ------------------------------------------------------------------
    def validate_blobs(
        self,
        repo_id: str,
        repo_type: str,
        objects: list[dict[str, Any]],
    ) -> dict[str, str | None]:
        """Check which blobs need uploading via the LFS batch API.

        POST /api/v1/repos/{type}s/{repo_id}/info/lfs/objects/batch

        Returns mapping: sha256 → upload_url (if needs upload) or None (exists).
        """
        segment = _resolve_segment(repo_type)
        payload = {"operation": "upload", "objects": objects}
        resp = self._request(
            "POST",
            f"repos/{segment}/{repo_id}/info/lfs/objects/batch",
            json_body=payload,
        )
        data = self._json_data(resp)

        result: dict[str, str | None] = {}
        resp_objects = data.get("objects", []) if isinstance(data, dict) else []
        for obj in resp_objects:
            oid = obj.get("oid", "")
            actions = obj.get("actions", {})
            upload_action = actions.get("upload", {})
            href = upload_action.get("href")
            result[oid] = href  # None means already exists
        return result

    def upload_blob(
        self,
        upload_url: str,
        data: Union[str, bytes, BinaryIO, IO[bytes]],
        size: int,
        *,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Upload a blob to the presigned URL returned by :meth:`validate_blobs`.

        PUT {upload_url}

        Sends both ``Authorization: Bearer`` and ``Cookie: m_session_id``
        headers to authenticate against the LFS domain (which may differ
        from the main API domain).

        Returns the parsed JSON response body on success.
        """
        upload_headers: dict[str, str] = {
            "Content-Length": str(size),
            "X-Request-ID": uuid.uuid4().hex,
        }
        if self._token:
            upload_headers["Authorization"] = f"Bearer {self._token}"
            upload_headers["Cookie"] = f"m_session_id={self._token}"
        if headers:
            upload_headers.update(headers)

        try:
            resp = self._session.put(
                upload_url,
                data=data,
                headers=upload_headers,
                timeout=timeout or (UPLOAD_BLOB_CONNECT_TIMEOUT, UPLOAD_BLOB_READ_TIMEOUT),
            )
        except requests.ConnectionError as exc:
            raise NetworkError(f"Blob upload connection failed: {exc}") from exc
        except requests.Timeout as exc:
            raise RequestTimeoutError(f"Blob upload timed out: {exc}") from exc

        raise_for_status(resp)

        # Presigned URLs (cloud storage) may return empty bodies on success.
        try:
            body = resp.json()
        except (ValueError, RuntimeError):
            return {}
        if isinstance(body, dict) and body.get("Code") not in (200, "200", None):
            from .errors import APIError
            raise APIError(
                body.get("Message") or body.get("message") or f"Blob upload failed (Code={body.get('Code')})",
                status_code=resp.status_code,
                response_body=body,
                url=upload_url,
                method="PUT",
            )
        return body

    # ------------------------------------------------------------------
    # Raw Download URL
    # ------------------------------------------------------------------
    def get_download_url(
        self,
        repo_id: str,
        repo_type: str,
        file_path: str,
        revision: str = "master",
    ) -> str:
        """Construct the file download URL (no request is made).

        URL pattern: {endpoint}/api/v1/{type}s/{repo_id}/repo?Revision={rev}&FilePath={path}
        """
        segment = _resolve_segment(repo_type)
        return (
            f"{self._endpoint}{LEGACY_API_PREFIX}/{segment}/{repo_id}/repo"
            f"?Revision={quote_plus(revision)}&FilePath={quote_plus(file_path)}"
        )

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------
    def get_collection(
        self,
        collection_id: str,
        *,
        element_type: str = "skill",
        page_number: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Get collection details and its elements.

        GET /api/v1/collections?Fid=...&ElementType=...
        """
        params = {
            "Fid": collection_id,
            "ElementType": element_type,
            "PageNumber": page_number,
            "PageSize": page_size,
        }
        resp = self._request("GET", "collections", params=params)
        return self._json_data(resp)

    # ------------------------------------------------------------------
    # Archive Download (skill repos)
    # ------------------------------------------------------------------
    def download_archive(
        self,
        repo_id: str,
        repo_type: str,
        revision: str = "master",
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        """Download the entire repo as a zip archive.

        GET /api/v1/{type}s/{repo_id}/archive/zip/{revision}

        Skills (and potentially other repo types) do not support per-file
        download via ``/repo?FilePath=...``.  This method streams the
        archive endpoint instead.
        """
        segment = _resolve_segment(repo_type)
        return self._request(
            "GET",
            f"{segment}/{repo_id}/archive/zip/{revision}",
            headers=headers,
            stream=True,
        )

    # ------------------------------------------------------------------
    # Raw Download URL
    # ------------------------------------------------------------------
    def download_stream(
        self,
        repo_id: str,
        repo_type: str,
        file_path: str,
        revision: str = "master",
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        """Start a streaming download of a file.

        Returns a Response with stream=True for chunked reading.
        """
        segment = _resolve_segment(repo_type)
        params = {"Revision": revision, "FilePath": file_path}
        return self._request(
            "GET",
            f"{segment}/{repo_id}/repo",
            params=params,
            headers=headers,
            stream=True,
        )
