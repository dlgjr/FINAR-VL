"""Legacy-compatible single-file download wrappers.

These functions replicate the signature of the old
``modelscope.hub.file_download`` module.
"""

from __future__ import annotations

import warnings

import requests as _requests

from ..api import HubApi
from ..constants import RepoType
from ..errors import AuthenticationError, NotExistError, PermissionDeniedError
from .constants import DEFAULT_DATASET_REVISION


def _resolve_legacy_paths(
    repo_id: str,
    cache_dir: str | None,
    local_dir: str | None,
    api: "HubApi",
) -> tuple[str | None, str | None]:
    """Resolve cache_dir/local_dir for legacy API compatibility.

    Passes parameters through so the new API uses its standard cache
    layout (``{cache}/{type}s/{owner}--{name}/snapshots/{rev}/...``),
    consistent with CLI ``ms download`` behavior.

    When ``local_dir`` is explicitly set, files go directly there.
    Otherwise the standard cache hierarchy is used.
    """
    return cache_dir, local_dir


def model_file_download(
    model_id: str,
    file_path: str,
    revision: str | None = None,
    *,
    cache_dir: str | None = None,
    local_dir: str | None = None,
    cookies: dict | None = None,
    token: str | None = None,
    endpoint: str | None = None,
    local_files_only: bool = False,
    user_agent: dict | str | None = None,
) -> str:
    """Download a single model file (legacy signature)."""
    if cookies is not None:
        warnings.warn(
            "The 'cookies' parameter is deprecated and ignored. Use 'token' instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    api = HubApi(token=token, endpoint=endpoint)
    if endpoint is None and not local_files_only:
        try:
            endpoint = api.resolve_endpoint_for_read(model_id, repo_type="model")
            api = HubApi(token=token, endpoint=endpoint)
        except Exception:
            pass
    effective_cache, effective_local = _resolve_legacy_paths(
        model_id, cache_dir, local_dir, api,
    )
    try:
        result = api.download_file(
            model_id,
            repo_type=RepoType.MODEL,
            file_path=file_path,
            revision=revision,
            cache_dir=effective_cache,
            local_dir=effective_local,
            local_files_only=local_files_only,
            user_agent=user_agent,
        )
    except (NotExistError, AuthenticationError, PermissionDeniedError) as e:
        raise _requests.exceptions.HTTPError(
            str(e), response=getattr(e, 'response', None)
        ) from e
    return str(result)


def dataset_file_download(
    dataset_id: str,
    file_path: str,
    *,
    cache_dir: str | None = None,
    local_dir: str | None = None,
    revision: str | None = None,
    cookies: dict | None = None,
    token: str | None = None,
    endpoint: str | None = None,
    local_files_only: bool = False,
    user_agent: dict | str | None = None,
) -> str:
    """Download a single dataset file (legacy signature)."""
    if cookies is not None:
        warnings.warn(
            "The 'cookies' parameter is deprecated and ignored. Use 'token' instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    api = HubApi(token=token, endpoint=endpoint)
    if endpoint is None and not local_files_only:
        try:
            endpoint = api.resolve_endpoint_for_read(dataset_id, repo_type="dataset")
            api = HubApi(token=token, endpoint=endpoint)
        except Exception:
            pass
    effective_cache, effective_local = _resolve_legacy_paths(
        dataset_id, cache_dir, local_dir, api,
    )
    try:
        result = api.download_file(
            dataset_id,
            repo_type=RepoType.DATASET,
            file_path=file_path,
            revision=revision or DEFAULT_DATASET_REVISION,
            cache_dir=effective_cache,
            local_dir=effective_local,
            local_files_only=local_files_only,
            user_agent=user_agent,
        )
    except (NotExistError, AuthenticationError, PermissionDeniedError) as e:
        raise _requests.exceptions.HTTPError(
            str(e), response=getattr(e, 'response', None)
        ) from e
    return str(result)
