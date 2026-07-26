# Copyright (c) Alibaba, Inc. and its affiliates.
"""HTTP client for ModelScope Hub agent-repository API.

Endpoints:

* ``GET  /openapi/v1/users/me``                            -> login
* ``GET  /openapi/v1/agents/{path}/{name}``                -> repo metadata
* ``POST /openapi/v1/agents``                              -> create empty agent
* ``GET  /api/v1/agents/{path}/{name}/repo/files``         -> list files
* ``GET  /agents/{path}/{name}/resolve/{rev}/{file}``      -> file download
* ``POST /api/v1/repos/agents/{id}/commit/{rev}``          -> commit files (normal/lfs)
* ``POST /api/v1/repos/agents/{id}/info/lfs/objects/batch`` -> LFS batch verify
* ``DELETE /api/v1/agents/{path}/{name}/repo/file``        -> delete file
"""
from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass

import requests

from ..config import HubConfig
from ..constants import Visibility
from ..errors import APIError, HubError, NotExistError
from .._openapi import OpenAPIClient

logger = logging.getLogger("modelscope_hub.agent")

# LFS file extensions that must use LFS upload pathway.
_LFS_EXTENSIONS: frozenset[str] = frozenset({
    ".7z", ".aac", ".arrow", ".audio", ".bin", ".bmp", ".bz2",
    ".ckpt", ".flac", ".ftz", ".gif", ".gz", ".h5",
    ".jack", ".jpeg", ".jpg", ".joblib", ".jsonl",
    ".lz4", ".mlmodel", ".model", ".mp3", ".mp4", ".msgpack",
    ".npy", ".npz", ".ogg", ".onnx", ".ot",
    ".parquet", ".pb", ".pcm", ".pickle", ".pkl", ".png",
    ".pt", ".pth", ".rar", ".raw",
    ".safetensors", ".sam", ".tar", ".tflite", ".tgz", ".tiff",
    ".wasm", ".wav", ".webm", ".webp", ".xz", ".zip", ".zst",
})

# Files larger than this threshold (bytes) use LFS upload.
_LFS_SIZE_THRESHOLD: int = 1 * 1024 * 1024  # 1 MB


@dataclass
class RemoteFileInfo:
    """Metadata for a single file in the remote repository."""
    path: str
    sha256: str
    is_lfs: bool = False


def is_lfs_file(file_path: str, size: int) -> bool:
    """Determine whether a file should use LFS upload.

    A file is considered LFS if:
    1. Its extension is in the known LFS extension set, OR
    2. Its size exceeds the LFS threshold (1 MB).
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in _LFS_EXTENSIONS:
        return True
    if size > _LFS_SIZE_THRESHOLD:
        return True
    return False


class AgentApi:
    """HTTP client for ModelScope Hub agent-repository API.

    This is the primary programmatic interface for interacting with agent
    repositories on ModelScope Hub.

    Parameters
    ----------
    config : HubConfig or None
        Pre-built configuration. When provided, *endpoint* and *token* are
        ignored and the config is used directly.
    endpoint : str or None
        Hub API endpoint (fallback: HubConfig default).
    token : str or None
        API token (fallback: HubConfig default / ``ms login``).
    timeout : int
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        token: str | None = None,
        timeout: int = 60,
        *,
        config: HubConfig | None = None,
    ):
        self._config = config or HubConfig(endpoint=endpoint, token=token)
        self.server = (self._config.endpoint or "").rstrip("/")
        self.token = self._config.token
        self.timeout = timeout
        self._openapi = OpenAPIClient(config=self._config, timeout=float(timeout))

    # ---- repository ----

    def repo_info(self, path: str, name: str) -> dict | None:
        """Repo metadata or None if the repo does not exist (404)."""
        try:
            return self._openapi.request("GET", f"/agents/{path}/{name}")
        except NotExistError:
            return None

    def check_repo(self, path: str, name: str) -> bool:
        """True if the repo exists, False on 404."""
        return self.repo_info(path, name) is not None

    def list_agents(self, owner: str | None = None, page_number: int = 1, page_size: int = 10) -> dict:
        """List agent repositories (PUT /api/v1/dolphin/agents).

        Queries the dolphin search endpoint. When *owner* is given it is sent as
        a ``Path contains`` criterion (the group filter). Returns a dict with
        'items' (list of agent metadata dicts) and 'total_count' (int).
        """
        criterion: list[dict] = []
        if owner:
            criterion.append({
                "Category": "Path",
                "Predicate": "contains",
                "StringValues": [owner],
            })
        body = {
            "PageSize": page_size,
            "PageNumber": page_number,
            "Query": "",
            "Sort": "Default",
            "Criterion": criterion,
        }
        list_url = f"{self.server}/api/v1/dolphin/agents"
        data = self._openapi.request(
            "PUT", url=list_url, json_body=body, require_token=False)
        if isinstance(data, list):
            return {"items": data, "total_count": len(data)}
        if isinstance(data, dict):
            items = next(
                (data[k] for k in ("AgentList", "Agents", "agents", "Data", "data")
                 if k in data),
                [],
            )
            if not isinstance(items, list):
                items = []
            total_val = next(
                (data[k] for k in ("TotalCount", "Total", "total_count")
                 if k in data and data[k] is not None),
                len(items),
            )
            try:
                total = int(total_val)
            except (ValueError, TypeError):
                total = len(items)
            return {"items": items, "total_count": total}
        return {"items": [], "total_count": 0}

    def create_repo(self, path: str, name: str, framework: str | None = None,
                    visibility: str = "public") -> dict:
        """Create an empty agent (POST /agents).

        The server creates a bare repository.  Files are added separately via
        :meth:`commit_files`.

        Args:
            framework: Optional product/framework identifier stored with the
                       repo (e.g. "qoder", "nanobot").  Defaults to server-side
                       default when omitted.
            visibility: Repository visibility, ``"public"`` (default) or
                        ``"private"``.
        """
        allowed = (Visibility.PUBLIC.label, Visibility.PRIVATE.label)
        if visibility not in allowed:
            raise ValueError(
                f"visibility must be one of {allowed}, got {visibility!r}")
        body: dict = {"path": path, "name": name, "visibility": visibility}
        if framework:
            body["framework"] = framework
        return self._openapi.request("POST", "/agents", json_body=body)

    def list_repo_files(self, path: str, name: str, revision: str = 'master') -> list[str]:
        """All file paths in the repo, recursing into sub-directories."""
        entries = self._fetch_tree_entries(path, name, revision)
        return [e["path"] for e in entries if e["type"] == "blob" and e["path"]]

    def list_repo_files_detail(self, path: str, name: str, revision: str = 'master') -> list[RemoteFileInfo]:
        """All blob files with sha256 and is_lfs flag."""
        entries = self._fetch_tree_entries(path, name, revision)
        results: list[RemoteFileInfo] = []
        for item in entries:
            if item["type"] != "blob" or not item["path"]:
                continue
            results.append(RemoteFileInfo(
                path=item["path"],
                sha256=item.get("sha256") or "",
                is_lfs=bool(item.get("is_lfs", False)),
            ))
        return results

    def _fetch_tree_entries(self, path: str, name: str, revision: str) -> list[dict]:
        """Fetch and normalize the repo file tree from the API (with pagination)."""
        page = 1
        page_size = 100
        max_pages = 50
        all_entries: list[dict] = []

        list_url = f"{self.server}/api/v1/agents/{path}/{name}/repo/files"
        while True:
            data = self._openapi.request(
                "GET", url=list_url,
                params={
                    "recursive": "true",
                    "page_size": str(page_size),
                    "page": str(page),
                    "revision": revision,
                },
            )

            raw = []
            if isinstance(data, dict):
                raw = data.get("Trees") or data.get("trees") or []
            elif isinstance(data, list):
                raw = data

            for item in raw:
                if not isinstance(item, dict):
                    continue
                all_entries.append({
                    "path": item.get("Path") or item.get("path") or "",
                    "type": item.get("Type") or item.get("type") or "",
                    "sha256": item.get("Sha256") or item.get("sha256") or "",
                    "is_lfs": bool(item.get("IsLfs") or item.get("is_lfs") or False),
                })

            if len(raw) < page_size:
                break
            page += 1
            if page > max_pages:
                logger.warning(
                    "Pagination limit reached (%d pages) for %s/%s; results may be incomplete.",
                    max_pages, path, name,
                )
                break

        return all_entries

    def download_repo_file(self, path: str, name: str, file_path: str,
                           revision: str = "master", *, binary: bool = False):
        """Download one repo file.

        Returns bytes when *binary=True*, otherwise str.
        """
        dl_url = f"{self.server}/agents/{path}/{name}/resolve/{revision}/{file_path}"
        resp = self._openapi.request("GET", url=dl_url, unwrap=False)
        return resp.content if binary else resp.text

    # ---- commit (normal + LFS) ----

    def commit_files(self, path: str, name: str, actions: list[dict],
                     revision: str = "master", commit_message: str = "sync") -> dict:
        """Commit file changes via POST /api/v1/repos/agents/{path}/{name}/commit/{revision}.

        Each action dict should contain:
          - action: "create" | "update" | "delete"
          - path: file path in repo
          - type: "normal" | "lfs"  (for create/update)
          - size: file size in bytes (for create/update)
          - sha256: sha256 hash (required for lfs; empty string for normal)
          - content: base64-encoded content (for normal) or empty (for lfs)
          - encoding: "base64" (for normal) or "" (for lfs)
        """
        commit_url = f"{self.server}/api/v1/repos/agents/{path}/{name}/commit/{revision}"
        body = {"commit_message": commit_message, "actions": actions}
        return self._openapi.request("POST", url=commit_url, json_body=body)

    def lfs_batch(self, path: str, name: str, oid: str, size: int) -> str | None:
        """LFS batch verify and return upload URL (or None if already exists).

        POST /api/v1/repos/agents/{path}/{name}/info/lfs/objects/batch
        Returns the upload href if the server needs the blob, None otherwise.
        """
        batch_url = (
            f"{self.server}/api/v1/repos/agents/{path}/{name}"
            f"/info/lfs/objects/batch"
        )
        body = {
            "operation": "upload",
            "objects": [{"oid": oid, "size": size}],
        }
        data = self._openapi.request("POST", url=batch_url, json_body=body)
        # Response: {"objects": [{"actions": {"upload": {"href": ...}}}]}
        # If no actions.upload -> blob already exists, skip PUT.
        objects = []
        if isinstance(data, dict):
            objects = data.get("objects") or []
        if not objects:
            return None
        upload_info = objects[0].get("actions", {}).get("upload", {})
        return upload_info.get("href") or None

    def lfs_upload_blob(self, upload_url: str, data: bytes) -> None:
        """PUT binary data to the LFS upload URL."""
        self._openapi.request(
            "PUT", url=upload_url,
            data=data,
            headers={"Content-Type": "application/octet-stream"},
            require_token=False,
            unwrap=False,
            timeout=max(self.timeout, 300),
        )

    def upload_lfs_file(self, path: str, name: str, file_path: str,
                        content: bytes, action: str = "create",
                        revision: str = "master",
                        commit_message: str = "sync") -> dict:
        """Full LFS upload flow: batch verify -> PUT blob -> commit reference.

        Combines lfs_batch + lfs_upload_blob + commit_files for one file.
        """
        oid = hashlib.sha256(content).hexdigest()
        size = len(content)

        # Step 1: batch verify
        upload_url = self.lfs_batch(path, name, oid, size)
        # Step 2: PUT blob if needed
        if upload_url:
            self.lfs_upload_blob(upload_url, content)

        # Step 3: commit LFS reference
        actions = [{
            "action": action,
            "path": file_path,
            "type": "lfs",
            "size": size,
            "sha256": oid,
            "content": "",
            "encoding": "",
        }]
        return self.commit_files(path, name, actions, revision=revision,
                                 commit_message=commit_message)

    def delete_file(self, path: str, name: str, file_path: str,
                    revision: str = "master",
                    commit_message: str | None = None) -> dict:
        """Delete a file from the repo.

        DELETE /api/v1/agents/{path}/{name}/repo/file
        """
        delete_url = f"{self.server}/api/v1/agents/{path}/{name}/repo/file"
        body = {
            "branch": revision,
            "file_path": file_path,
            "commit_message": commit_message or f"Delete {file_path}",
        }
        return self._openapi.request("DELETE", url=delete_url, json_body=body)
