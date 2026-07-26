"""Legacy-compatible snapshot download wrappers.

These functions replicate the signature of the old
``modelscope.hub.snapshot_download`` module so that existing user code
and the old SDK can delegate to ``modelscope_hub`` without changes.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Sequence

import requests as _requests

from ..api import HubApi
from ..constants import RepoType
from ..errors import AuthenticationError, NotExistError, PermissionDeniedError
from ..utils.patterns import normalize_patterns
from .constants import DEFAULT_DATASET_REVISION
from .file_download import _resolve_legacy_paths

if TYPE_CHECKING:
    from .._download import ProgressCallback


def snapshot_download(
    model_id: str | None = None,
    *,
    revision: str | None = None,
    cache_dir: str | None = None,
    local_dir: str | None = None,
    allow_file_pattern: Sequence[str] | str | None = None,
    ignore_file_pattern: Sequence[str] | str | None = None,
    allow_patterns: Sequence[str] | str | None = None,
    ignore_patterns: Sequence[str] | str | None = None,
    max_workers: int = 4,
    cookies: dict | None = None,
    repo_id: str | None = None,
    repo_type: str | None = None,
    token: str | None = None,
    endpoint: str | None = None,
    local_files_only: bool = False,
    user_agent: dict | str | None = None,
    progress_callbacks: list[type[ProgressCallback]] | None = None,
) -> str:
    """Download a repo snapshot (legacy signature).

    Parameters mirror the old ``modelscope.hub.snapshot_download.snapshot_download``.
    ``allow_patterns``/``ignore_patterns`` take priority over the
    ``allow_file_pattern``/``ignore_file_pattern`` aliases when both are set.
    ``progress_callbacks`` takes a list of :class:`ProgressCallback`
    subclasses (not instances); each is instantiated per file to report
    download progress.
    """
    effective_id = repo_id or model_id
    if not effective_id:
        from ..errors import InvalidParameter
        raise InvalidParameter("Please provide a valid model_id or repo_id")
    effective_type = repo_type or "model"

    if cookies is not None:
        warnings.warn(
            "The 'cookies' parameter is deprecated and ignored. Use 'token' instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    include = _normalize_pattern(allow_patterns) or _normalize_pattern(allow_file_pattern)
    exclude = _normalize_pattern(ignore_patterns) or _normalize_pattern(ignore_file_pattern)

    api = HubApi(token=token, endpoint=endpoint)
    if endpoint is None and not local_files_only:
        try:
            endpoint = api.resolve_endpoint_for_read(
                effective_id, repo_type=effective_type,
            )
            api = HubApi(token=token, endpoint=endpoint)
        except Exception:
            pass
    effective_cache, effective_local = _resolve_legacy_paths(
        effective_id, cache_dir, local_dir, api,
    )
    try:
        result = api.download_repo(
            effective_id,
            repo_type=effective_type,
            revision=revision,
            cache_dir=effective_cache,
            local_dir=effective_local,
            allow_patterns=include,
            ignore_patterns=exclude,
            max_workers=max_workers,
            local_files_only=local_files_only,
            user_agent=user_agent,
            progress_callbacks=progress_callbacks,
        )
    except (NotExistError, AuthenticationError, PermissionDeniedError) as e:
        raise _requests.exceptions.HTTPError(
            str(e), response=getattr(e, 'response', None)
        ) from e
    return str(result)


def dataset_snapshot_download(
    dataset_id: str,
    *,
    revision: str | None = None,
    cache_dir: str | None = None,
    local_dir: str | None = None,
    allow_file_pattern: Sequence[str] | str | None = None,
    ignore_file_pattern: Sequence[str] | str | None = None,
    allow_patterns: Sequence[str] | str | None = None,
    ignore_patterns: Sequence[str] | str | None = None,
    max_workers: int = 4,
    cookies: dict | None = None,
    token: str | None = None,
    endpoint: str | None = None,
    local_files_only: bool = False,
    user_agent: dict | str | None = None,
) -> str:
    """Download a dataset snapshot (legacy signature)."""
    if cookies is not None:
        warnings.warn(
            "The 'cookies' parameter is deprecated and ignored. Use 'token' instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    include = _normalize_pattern(allow_patterns) or _normalize_pattern(allow_file_pattern)
    exclude = _normalize_pattern(ignore_patterns) or _normalize_pattern(ignore_file_pattern)

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
        result = api.download_repo(
            dataset_id,
            repo_type=RepoType.DATASET,
            revision=revision or DEFAULT_DATASET_REVISION,
            cache_dir=effective_cache,
            local_dir=effective_local,
            allow_patterns=include,
            ignore_patterns=exclude,
            max_workers=max_workers,
            local_files_only=local_files_only,
            user_agent=user_agent,
        )
    except (NotExistError, AuthenticationError, PermissionDeniedError) as e:
        raise _requests.exceptions.HTTPError(
            str(e), response=getattr(e, 'response', None)
        ) from e
    return str(result)


def _normalize_pattern(pattern: Sequence[str] | str | None) -> list[str] | None:
    return normalize_patterns(pattern)
