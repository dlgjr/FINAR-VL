"""Legacy-compatible HubApi wrapper.

Provides the same interface as ``modelscope.hub.api.HubApi`` (old SDK) by
wrapping the new ``modelscope_hub.HubApi``.
"""

from __future__ import annotations

import os
import warnings
from collections import defaultdict
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import time

from ..api import HubApi
from ..constants import RepoType
from ..errors import (
    AlreadyExistsError,
    AuthenticationError,
    InvalidParameter,
    NotExistError,
    PermissionDeniedError,
    is_repo_exists_error,
)
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..types import PagedResult, RepoInfo

logger = get_logger("compat")

DEFAULT_DATASET_REVISION = "master"

META_FILES_FORMAT = {'.json', '.csv', '.jsonl', '.tsv', '.py'}


class LegacyHubApi:
    """Drop-in replacement for the old ``modelscope.hub.api.HubApi``.

    Accepts the old constructor signature and maps method calls to the
    new HubApi implementation.
    """

    _api: HubApi
    _endpoint: str | None

    def __init__(
        self,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> None:
        if endpoint and not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}"
        self._endpoint = endpoint
        self._api = HubApi(endpoint=endpoint, token=token)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def login(self, token: str) -> tuple[str | None, Any]:
        """Login with token (old style returns ``(git_token, cookies)``).

        Preserves the legacy return contract: a 2-tuple of
        ``(git_access_token, cookies)`` so that existing callers doing
        ``token, cookies = api.login(...)`` continue to work.
        """
        if not token:
            return (None, None)
        self._api.login(token)
        git_token = self._api._config.load_git_token() or token
        cookies = self._api.get_cookies()
        return (git_token, cookies)

    def get_cookies(self, access_token: str | None = None, cookies_required: bool = False):
        """Get cookies for legacy API authentication.

        Delegates to :meth:`HubApi.get_cookies`.
        """
        return self._api.get_cookies(access_token=access_token, cookies_required=cookies_required)

    # ------------------------------------------------------------------
    # Repository operations
    # ------------------------------------------------------------------
    def get_model(self, model_id: str, revision: str | None = None) -> dict:
        """Get model info as a raw dict.

        Parameters
        ----------
        model_id : str
            Model identifier, e.g. ``"owner/model_name"``.
        revision : str, optional
            Branch or tag to query. Reserved for future use.
        """
        info = self._api.get_repo(model_id, RepoType.MODEL, revision=revision)
        return _repo_info_to_dict(info)

    def get_model_files(self, model_id: str, recursive: bool = True) -> list[dict]:
        """List files in a model repo."""
        files = self._api.list_repo_files(model_id, RepoType.MODEL, recursive=recursive)
        return [{"Path": f.path, "Size": f.size} for f in files]

    def create_repo(
        self,
        repo_id: str,
        *,
        token: str | None = None,
        visibility: int | str | None = None,
        repo_type: str = "model",
        chinese_name: str | None = None,
        license: str | None = None,
        exist_ok: bool = False,
        create_default_config: bool = False,
        endpoint: str | None = None,
        **kwargs: Any,
    ) -> "RepoInfo | None":
        """Create a repository (legacy signature)."""
        api = self._api
        if token or endpoint:
            api = HubApi(token=token, endpoint=endpoint or self._endpoint)
        if create_default_config:
            kwargs["create_default_config"] = True
        try:
            return api.create_repo(
                repo_id,
                repo_type=repo_type,
                visibility=visibility,
                license=license,
                chinese_name=chinese_name,
                **kwargs,
            )
        except AlreadyExistsError:
            if exist_ok:
                return None
            raise
        except Exception as exc:
            if exist_ok and is_repo_exists_error(exc):
                return None
            raise

    def create_model(self, model_id: str, **kwargs: Any) -> str:
        """Create a model repo (legacy signature).

        Returns the model repository URL for backward compatibility.
        Converts authentication errors to ``ValueError`` for legacy callers.
        """
        # Pre-normalize: convert numeric string to int for backward compatibility
        visibility = kwargs.get("visibility")
        if isinstance(visibility, str) and visibility.isdigit():
            kwargs["visibility"] = int(visibility)
        try:
            self.create_repo(model_id, repo_type="model", **kwargs)
        except (AuthenticationError, InvalidParameter) as e:
            if _is_auth_related(e):
                raise ValueError(
                    "Token does not exist, please login first."
                ) from e
            raise
        ep = self._endpoint or self._api._config.endpoint
        return f"{ep}/models/{model_id}"

    def push_model(self, model_id: str, model_dir: str, **kwargs: Any) -> None:
        """Upload a model directory (legacy signature)."""
        # Pre-validate model_dir
        if not os.path.isdir(model_dir):
            raise ValueError(
                f"model_dir '{model_dir}' does not exist or is not a directory."
            )
        config_files = ("configuration.json", "configuration.yaml", "configuration.yml")
        if not any(os.path.isfile(os.path.join(model_dir, f)) for f in config_files):
            logger.warning(
                "No model configuration file found in '%s'. "
                "Expected one of: %s. The upload will proceed, "
                "but the directory may not contain a valid model.",
                model_dir,
                ", ".join(config_files),
            )

        # Pre-normalize: convert numeric string to int for backward compatibility
        visibility = kwargs.get("visibility")
        if isinstance(visibility, str) and visibility.isdigit():
            kwargs["visibility"] = int(visibility)
        try:
            try:
                self._api.create_repo(
                    model_id,
                    repo_type=RepoType.MODEL,
                    visibility=kwargs.get("visibility"),
                    license=kwargs.get("license"),
                    chinese_name=kwargs.get("chinese_name"),
                )
            except AlreadyExistsError:
                logger.info("Repository '%s' already exists, proceeding with upload.", model_id)
            except Exception as exc:
                if not is_repo_exists_error(exc):
                    raise
                logger.info("Repository '%s' already exists, proceeding with upload.", model_id)
            self._api.upload_folder(
                model_id,
                RepoType.MODEL,
                model_dir,
                path_in_repo=kwargs.get("path_in_repo", ""),
                commit_message=kwargs.get("commit_message"),
                commit_description=kwargs.get("commit_description"),
                revision=kwargs.get("revision"),
                allow_patterns=kwargs.get("allow_patterns"),
                ignore_patterns=kwargs.get("ignore_patterns"),
                max_workers=kwargs.get("max_workers", 4),
                use_cache=kwargs.get("use_cache", True),
            )
        except (AuthenticationError, InvalidParameter) as e:
            if _is_auth_related(e):
                raise ValueError(
                    "Token does not exist, please login first."
                ) from e
            raise

    # ------------------------------------------------------------------
    # Endpoint resolution
    # ------------------------------------------------------------------
    def get_endpoint_for_read(
        self,
        repo_id: str,
        *,
        repo_type: str | None = None,
        token: str | None = None,
    ) -> str:
        """Resolve the best endpoint for read operations.

        Backward-compatible with the old SDK's ``get_endpoint_for_read()``.
        Honors ``MODELSCOPE_ENDPOINT`` (or deprecated ``MODELSCOPE_DOMAIN``)
        and ``MODELSCOPE_PREFER_AI_SITE`` env vars.
        """
        return self._api.resolve_endpoint_for_read(
            repo_id, repo_type=repo_type or "model", token=token,
        )

    def repo_exists(
        self,
        repo_id: str,
        *,
        repo_type: str | None = None,
        endpoint: str | None = None,
        re_raise: bool = False,
        token: str | None = None,
    ) -> bool:
        """Check if a repo exists (legacy signature with endpoint/token override)."""
        api = self._api
        if endpoint is not None or token is not None:
            api = HubApi(
                endpoint=endpoint or self._api._config.endpoint,
                token=token or self._api._config.token,
            )
        try:
            return api.repo_exists(repo_id, repo_type or "model")
        except Exception:
            if re_raise:
                raise
            return False

    def list_repos(
        self,
        repo_type: str | RepoType,
        *,
        owner: str | None = None,
        search: str | None = None,
        sort: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        **filters: Any,
    ) -> "PagedResult[RepoInfo]":
        """List repositories of the given type.

        Delegates to :meth:`HubApi.list_repos`.
        """
        return self._api.list_repos(
            repo_type,
            owner=owner,
            search=search,
            sort=sort,
            page_number=page_number,
            page_size=page_size,
            **filters,
        )

    def get_repo(
        self,
        repo_id: str,
        repo_type: str | RepoType,
        *,
        revision: str | None = None,
    ) -> "RepoInfo":
        """Get repository information.

        Delegates to :meth:`HubApi.get_repo`.
        """
        return self._api.get_repo(repo_id, repo_type, revision=revision)

    # ------------------------------------------------------------------
    # Download operations
    # ------------------------------------------------------------------
    def download_model(
        self,
        model_id: str,
        revision: str | None = None,
        cache_dir: str | None = None,
        local_dir: str | None = None,
    ) -> str:
        """Download a model snapshot."""
        import requests as _requests

        try:
            result = self._api.download_repo(
                model_id,
                repo_type=RepoType.MODEL,
                revision=revision,
                cache_dir=cache_dir,
                local_dir=local_dir,
            )
        except (NotExistError, AuthenticationError, PermissionDeniedError) as e:
            raise _requests.exceptions.HTTPError(
                str(e), response=getattr(e, 'response', None)
            ) from e
        return str(result)

    # ------------------------------------------------------------------
    # Studio operations
    # ------------------------------------------------------------------
    def deploy_studio(self, studio_id: str, **kwargs: Any) -> dict:
        return self._api.deploy_repo(
            studio_id, RepoType.STUDIO, payload=kwargs.get("payload"),
        )

    def stop_studio(self, studio_id: str, **kwargs: Any) -> dict:
        return self._api.stop_repo(studio_id, RepoType.STUDIO)

    def get_studio_logs(self, studio_id: str, **kwargs: Any) -> dict:
        return self._api.get_repo_logs(studio_id, RepoType.STUDIO, **kwargs)

    def update_studio_settings(self, studio_id: str, **kwargs: Any) -> dict:
        return self._api.update_repo_settings(studio_id, RepoType.STUDIO, **kwargs)

    def list_studio_secrets(self, studio_id: str, **kwargs: Any) -> list:
        return self._api.list_secrets(studio_id, RepoType.STUDIO)

    def add_studio_secret(self, studio_id: str, key: str, value: str, **kwargs: Any) -> None:
        self._api.add_secret(studio_id, key, value, RepoType.STUDIO)

    def update_studio_secret(self, studio_id: str, key: str, value: str, **kwargs: Any) -> None:
        self._api.update_secret(studio_id, key, value, RepoType.STUDIO)

    def delete_studio_secret(self, studio_id: str, key: str, **kwargs: Any) -> None:
        self._api.delete_secret(studio_id, key, RepoType.STUDIO)

    # ------------------------------------------------------------------
    # Revision resolution
    # ------------------------------------------------------------------
    def get_model_branches_and_tags_details(
        self, model_id: str, **kwargs: Any,
    ) -> tuple[list[dict], list[dict]]:
        """Get model branches and tags as two separate detail lists.

        Returns ``(branches_detail, tags_detail)`` where each item is a dict
        with at least ``Revision`` and ``CreatedAt`` keys.
        """
        return self._api.legacy.list_revisions_detail(model_id, "model")

    def get_model_branches_and_tags(
        self, model_id: str, **kwargs: Any,
    ) -> tuple[list[str], list[str]]:
        """Get model branch and tag names."""
        branches_detail, tags_detail = self.get_model_branches_and_tags_details(model_id)
        branches = [x["Revision"] for x in branches_detail] if branches_detail else []
        tags = [x["Revision"] for x in tags_detail] if tags_detail else []
        return branches, tags

    def get_valid_revision_detail(
        self,
        model_id: str,
        revision: str | None = None,
        cookies: Any = None,
        endpoint: str | None = None,
        *,
        release_timestamp: int | None = None,
    ) -> dict:
        """Resolve a model revision to a concrete branch/tag detail dict.

        Replicates the old ``modelscope.hub.api.HubApi.get_valid_revision_detail``
        behavior.  When *release_timestamp* is supplied (the old SDK passes
        ``modelscope.version.__release_datetime__`` converted to epoch seconds),
        the full version-selection logic is used:

        * **Dev mode** (``release_timestamp > now + 1 year``): default to
          ``master``, validate existence.
        * **Release mode**: pick the newest tag whose ``CreatedAt <=
          release_timestamp``, fall back to ``master`` if none match.

        Without *release_timestamp* the simplified rule applies: explicit
        *revision* is validated, ``None`` defaults to ``master``.
        """
        _ONE_YEAR = 365 * 24 * 60 * 60

        branches_detail, tags_detail = self.get_model_branches_and_tags_details(model_id)
        all_branches = [x["Revision"] for x in branches_detail] if branches_detail else []
        all_tags = [x["Revision"] for x in tags_detail] if tags_detail else []

        def _find(details: list[dict], name: str) -> dict | None:
            for item in details:
                if item.get("Revision") == name:
                    return item
            return None

        def _created_at(tag: dict) -> int:
            """Safely coerce CreatedAt to epoch seconds (handles str, float, ms, None)."""
            raw = tag.get("CreatedAt")
            if raw is None:
                return 0
            try:
                ts = int(float(raw))
            except (TypeError, ValueError):
                return 0
            # Normalize millisecond timestamps to seconds
            if ts > 9_999_999_999:
                ts = ts // 1000
            return ts

        # --- Dev mode or no release_timestamp ---------------------------------
        if release_timestamp is None or release_timestamp > int(time.time()) + _ONE_YEAR:
            if revision is None:
                revision = "master"
            if revision not in all_branches and revision not in all_tags:
                raise NotExistError(
                    f"The model: {model_id} has no revision: {revision}"
                )
            detail = _find(tags_detail, revision) or _find(branches_detail, revision)
            return detail or {"Revision": revision}

        # --- Release mode -----------------------------------------------------
        # Explicit branch name → return immediately
        if revision is not None and revision in all_branches:
            return _find(branches_detail, revision) or {"Revision": revision}

        # No tags at all → master (or validate explicit revision)
        if not tags_detail:
            if revision is None or revision == "master":
                return _find(branches_detail, "master") or {"Revision": "master"}
            raise NotExistError(
                f"The model: {model_id} has no revision: {revision}"
            )

        # Has tags
        if revision is None:
            candidates = [
                t for t in tags_detail
                if _created_at(t) <= release_timestamp
            ]
            if candidates:
                return max(candidates, key=_created_at)
            return _find(branches_detail, "master") or {"Revision": "master"}

        # Explicit revision
        if revision in all_tags:
            return _find(tags_detail, revision) or {"Revision": revision}
        if revision == "master":
            return _find(branches_detail, "master") or {"Revision": "master"}
        valid = ", ".join(all_tags)
        raise NotExistError(
            f"The model: {model_id} has no revision: {revision} "
            f"(valid tags: {valid})"
        )

    def get_valid_revision(
        self,
        model_id: str,
        revision: str | None = None,
        cookies: Any = None,
        endpoint: str | None = None,
    ) -> str:
        """Resolve a model revision to a concrete revision string."""
        return self.get_valid_revision_detail(
            model_id, revision=revision, cookies=cookies, endpoint=endpoint,
        )["Revision"]

    # ------------------------------------------------------------------
    # Collection / Skills
    # ------------------------------------------------------------------
    def get_collection(self, collection_id: str, **kwargs: Any) -> dict:
        """Fetch collection data — delegates to legacy API."""
        return self._api.legacy.get_collection(collection_id)

    def download_skill(self, skill_id: str, local_dir: str | None = None, **kwargs: Any) -> str:
        """Download a skill to local directory."""
        result = self._api.download_repo(
            skill_id,
            repo_type=RepoType.SKILL,
            local_dir=local_dir,
        )
        return str(result)

    # ------------------------------------------------------------------
    # Type-specific list/create/get/delete (old SDK compatibility)
    # ------------------------------------------------------------------
    _OPENAPI_MAX_PAGE_SIZE = 50

    def list_models(
        self,
        owner_or_group: str,
        page_number: int = 1,
        page_size: int = 10,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> dict:
        """List models owned by a user/org."""
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)
        page = api.list_repos(
            RepoType.MODEL,
            owner=owner_or_group,
            page_number=page_number,
            page_size=min(page_size, self._OPENAPI_MAX_PAGE_SIZE),
        )
        return {
            "Models": [_repo_info_to_dict(r) for r in page.items],
            "TotalCount": page.total_count,
        }

    def list_datasets(
        self,
        owner: str | None = None,
        page_size: int = 50,
        page_number: int = 1,
        *,
        owner_or_group: str | None = None,
        sort: str | None = None,
        search: str | None = None,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> "PagedResult":
        """List datasets owned by a user/org.

        .. deprecated::
            Use ``list_repos(owner, repo_type='dataset')`` instead.

        Parameters
        ----------
        owner : str, optional
            Filter by owner (aligned with ``list_repos``'s ``owner`` param).
        page_size : int, optional
            Items per page. Default is 50.
        page_number : int, optional
            1-based page index. Default is 1.
        owner_or_group : str, optional
            **Deprecated** alias for ``owner``. Kept for backward compatibility.
        sort : str, optional
            Sort key (e.g. ``"downloads"``).
        search : str, optional
            Free-text search query.
        endpoint : str, optional
            Override API endpoint.
        token : str, optional
            Override API token.
        """
        warnings.warn(
            "list_datasets() is deprecated, use list_repos(owner, repo_type='dataset') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Resolve owner: explicit 'owner' takes precedence over deprecated alias
        actual_owner = owner or owner_or_group
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)
        return api.list_repos(
            RepoType.DATASET,
            owner=actual_owner,
            search=search,
            sort=sort,
            page_number=page_number,
            page_size=min(page_size, self._OPENAPI_MAX_PAGE_SIZE),
        )

    def create_dataset(
        self,
        dataset_name: str,
        namespace: str,
        chinese_name: str = "",
        license: str = "Apache License 2.0",
        visibility: int = 1,
        description: str = "",
        endpoint: str | None = None,
        token: str | None = None,
    ) -> str:
        """Create a dataset repository, return its URL."""
        repo_id = f"{namespace}/{dataset_name}"
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)
        api.create_repo(
            repo_id,
            repo_type=RepoType.DATASET,
            visibility=visibility,
            license=license,
            chinese_name=chinese_name,
        )
        ep = endpoint or self._endpoint or api._config.endpoint
        return f"{ep}/datasets/{namespace}/{dataset_name}"

    def get_dataset(
        self,
        dataset_id: str,
        revision: str | None = None,
        *,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> "RepoInfo":
        """Get dataset information via OpenAPI.

        .. deprecated::
            Use ``get_repo(repo_id, repo_type='dataset')`` instead.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier (corresponds to ``repo_id`` in ``get_repo``).
        revision : str, optional
            Branch or tag to query (aligned with ``get_repo``'s ``revision``).
        endpoint : str, optional
            Override API endpoint.
        token : str, optional
            Override API token.
        """
        warnings.warn(
            "get_dataset() is deprecated, use get_repo(repo_id, repo_type='dataset') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)
        return api.get_repo(dataset_id, RepoType.DATASET, revision=revision)

    def delete_model(
        self,
        model_id: str,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> None:
        """Delete a model repository."""
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)
        api.delete_repo(model_id, RepoType.MODEL)

    def delete_dataset(
        self,
        dataset_id: str,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> None:
        """Delete a dataset repository."""
        warnings.warn(
            "This function is deprecated due to security reasons, "
            "and will be recovered in future versions with proper token authentication.",
            DeprecationWarning,
            stacklevel=2,
        )
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)
        api.delete_repo(dataset_id, RepoType.DATASET)

    def get_dataset_files(
        self,
        repo_id: str,
        *,
        revision: str = DEFAULT_DATASET_REVISION,
        root_path: str = "/",
        recursive: bool = True,
        page_number: int = 1,
        page_size: int = 100,
        endpoint: str | None = None,
        token: str | None = None,
        dataset_hub_id: str | None = None,
    ) -> list:
        """Get dataset file tree via the datahub API."""
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)

        if dataset_hub_id is None:
            if "/" in repo_id:
                _owner, _name = repo_id.split("/", 1)
            else:
                raise ValueError(f"Invalid repo_id: {repo_id}")
            dataset_hub_id, _ = self.get_dataset_id_and_type(
                dataset_name=_name, namespace=_owner, endpoint=endpoint, token=token)

        params: dict[str, Any] = {
            "Revision": revision,
            "Root": root_path,
            "Recursive": "True" if recursive else "False",
            "PageNumber": page_number,
            "PageSize": page_size,
        }
        resp = api.legacy._request(
            "GET", f"datasets/{dataset_hub_id}/repo/tree", params=params)
        data = api.legacy._json_data(resp)
        if isinstance(data, dict):
            return data.get("Files") or []
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # Datahub-specific methods (raw HTTP via legacy client)
    # ------------------------------------------------------------------
    _dataset_id_type_cache: dict = {}

    def get_dataset_id_and_type(
        self,
        dataset_name: str,
        namespace: str,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> tuple:
        """Get the dataset hub-internal id and type."""
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)

        cache_key = (namespace, dataset_name, endpoint or self._endpoint)
        cached = LegacyHubApi._dataset_id_type_cache.get(cache_key)
        if cached is not None:
            return cached

        data = api.legacy.get_repo_info(f"{namespace}/{dataset_name}", RepoType.DATASET)
        dataset_id = data["Id"]
        dataset_type = data["Type"]
        LegacyHubApi._dataset_id_type_cache[cache_key] = (dataset_id, dataset_type)
        return dataset_id, dataset_type

    def get_dataset_meta_file_list(
        self,
        dataset_name: str,
        namespace: str,
        dataset_id: str,
        revision: str,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> list:
        """Get the meta file-list of the dataset."""
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)

        params = {"Revision": revision}
        resp = api.legacy._request(
            "GET", f"datasets/{dataset_id}/repo/tree", params=params)
        data = api.legacy._json_data(resp)
        if data is None:
            raise NotExistError(
                f"The modelscope dataset [dataset_name = {dataset_name}, "
                f"namespace = {namespace}, version = {revision}] does not exist")
        file_list = data.get("Files") if isinstance(data, dict) else data
        if file_list is None:
            raise NotExistError(
                f"The modelscope dataset [dataset_name = {dataset_name}, "
                f"namespace = {namespace}, version = {revision}] does not exist")
        return file_list

    @staticmethod
    def dump_datatype_file(dataset_type: int, meta_cache_dir: str) -> None:
        """Dump dataset type marker file for offline formation detection."""
        from modelscope.utils.constant import DatasetFormations
        ext = DatasetFormations.formation_mark_ext.value
        dataset_type_file_path = os.path.join(
            meta_cache_dir, f"{str(dataset_type)}{ext}")
        with open(dataset_type_file_path, "w") as fp:
            fp.write("*** Automatically-generated file, do not modify ***")

    def get_dataset_meta_files_local_paths(
        self,
        dataset_name: str,
        namespace: str,
        revision: str,
        meta_cache_dir: str,
        dataset_type: int,
        file_list: list,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> tuple:
        """Download meta files and return local paths grouped by extension."""
        from modelscope.utils.constant import DatasetFormations, DatasetMetaFormats

        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)

        local_paths: dict[str, list] = defaultdict(list)
        dataset_formation = DatasetFormations(dataset_type)
        dataset_meta_format = DatasetMetaFormats[dataset_formation]

        self.dump_datatype_file(dataset_type=dataset_type, meta_cache_dir=meta_cache_dir)

        for file_info in file_list:
            file_path = file_info["Path"]
            extension = os.path.splitext(file_path)[-1]
            if extension not in dataset_meta_format:
                continue
            resp = api.legacy._request(
                "GET",
                f"datasets/{namespace}/{dataset_name}/repo",
                params={"Revision": revision, "FilePath": file_path},
            )
            local_path = os.path.join(meta_cache_dir, file_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            if os.path.exists(local_path):
                local_paths[extension].append(local_path)
                continue
            with open(local_path, "wb") as f:
                f.write(resp.content)
            local_paths[extension].append(local_path)

        return local_paths, dataset_formation

    def get_file_base_path(
        self,
        repo_id: str,
        endpoint: str | None = None,
    ) -> str:
        """Return the base URL prefix for dataset file downloads."""
        if "/" not in repo_id:
            raise ValueError(f"Invalid repo_id format, expected 'namespace/name': {repo_id!r}")
        namespace, dataset_name = repo_id.split("/", 1)
        ep = endpoint or self._endpoint or self._api._config.endpoint
        return f"{ep}/api/v1/datasets/{namespace}/{dataset_name}/repo?"

    def get_dataset_file_url(
        self,
        file_name: str,
        dataset_name: str,
        namespace: str,
        revision: str | None = DEFAULT_DATASET_REVISION,
        view: bool = False,
        extension_filter: bool = True,
        endpoint: str | None = None,
    ) -> str:
        """Construct the download URL for a dataset file."""
        if not file_name or not dataset_name or not namespace:
            raise ValueError("Args (file_name, dataset_name, namespace) cannot be empty!")
        ep = endpoint or self._endpoint or self._api._config.endpoint
        params = urlencode({
            "Source": "SDK",
            "Revision": revision,
            "FilePath": file_name,
            "View": view,
        })
        return f"{ep}/api/v1/datasets/{namespace}/{dataset_name}/repo?{params}"

    def get_dataset_file_url_origin(
        self,
        file_name: str,
        dataset_name: str,
        namespace: str,
        revision: str | None = DEFAULT_DATASET_REVISION,
        endpoint: str | None = None,
    ) -> str:
        """Get dataset file URL, resolving meta files to API URLs."""
        ep = endpoint or self._endpoint or self._api._config.endpoint
        if file_name and os.path.splitext(file_name)[-1] in META_FILES_FORMAT:
            file_name = (
                f"{ep}/api/v1/datasets/{namespace}/{dataset_name}/repo?"
                f"Revision={revision}&FilePath={file_name}"
            )
        return file_name

    def get_dataset_access_config(
        self,
        dataset_name: str,
        namespace: str,
        revision: str | None = DEFAULT_DATASET_REVISION,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> dict:
        """Get STS token config for dataset OSS access."""
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)
        resp = api.legacy._request(
            "GET",
            f"datasets/{namespace}/{dataset_name}/ststoken",
            params={"Revision": revision},
        )
        return api.legacy._json_data(resp)

    def get_dataset_access_config_session(
        self,
        dataset_name: str,
        namespace: str,
        check_cookie: bool = False,
        revision: str | None = DEFAULT_DATASET_REVISION,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> dict:
        """Get STS token config with session-based auth."""
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)
        resp = api.legacy._request(
            "GET",
            f"datasets/{namespace}/{dataset_name}/ststoken",
            params={"Revision": revision},
        )
        return api.legacy._json_data(resp)

    def get_dataset_access_config_for_unzipped(
        self,
        dataset_name: str,
        namespace: str,
        revision: str,
        zip_file_name: str,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> dict:
        """Get STS config for unzipped dataset files."""
        api = self._api
        if token:
            api = HubApi(endpoint=endpoint or self._endpoint, token=token)

        # Get visibility
        data = api.legacy.get_repo_info(f"{namespace}/{dataset_name}", RepoType.DATASET)
        visibility_map = {1: "private", 3: "internal", 5: "public"}
        visibility = visibility_map.get(data.get("Visibility", 5), "public")

        # Get STS token
        resp = api.legacy._request(
            "GET",
            f"datasets/{namespace}/{dataset_name}/ststoken",
            params={"Revision": revision},
        )
        data_sts = api.legacy._json_data(resp)
        file_dir = f"{visibility}-unzipped/{namespace}_{dataset_name}_{zip_file_name}"
        data_sts["Dir"] = file_dir
        return data_sts

    def dataset_download_statistics(
        self,
        dataset_name: str,
        namespace: str,
        use_streaming: bool = False,
        endpoint: str | None = None,
        token: str | None = None,
    ) -> None:
        """Report dataset download for statistics."""
        is_ci_test = os.getenv("CI_TEST") == "True"
        if not dataset_name or not namespace or is_ci_test or use_streaming:
            return
        try:
            api = self._api
            if token:
                api = HubApi(endpoint=endpoint or self._endpoint, token=token)
            api.legacy._request(
                "POST",
                f"datasets/{namespace}/{dataset_name}/download/increase",
            )
        except Exception:
            pass


_LEGACY_KEY_MAP: dict[str, str] = {
    "id": "Id",
    "owner": "Owner",
    "name": "Name",
    "repo_type": "RepoType",
    "visibility": "Visibility",
    "description": "Description",
    "downloads": "Downloads",
    "likes": "Likes",
    "created_at": "CreatedAt",
    "updated_at": "UpdatedAt",  # backward compat if manually constructed
    "last_modified": "UpdatedAt",
    "license": "License",
    "tags": "Tags",
}


def _repo_info_to_dict(info: Any) -> dict:
    """Convert a RepoInfo to a plain dict with legacy PascalCase keys."""
    if hasattr(info, "__dataclass_fields__"):
        from dataclasses import asdict
        raw = asdict(info)
    elif hasattr(info, "__dict__"):
        raw = {k: v for k, v in info.__dict__.items() if not k.startswith("_")}
    else:
        return {}
    return {_LEGACY_KEY_MAP.get(k, k): v for k, v in raw.items()}


def _is_auth_related(exc: Exception) -> bool:
    """Return True if the exception is authentication/login related."""
    if isinstance(exc, AuthenticationError):
        return True
    msg = str(exc).lower()
    return any(kw in msg for kw in ("login", "logged", "token", "unauthorized", "未登录"))
