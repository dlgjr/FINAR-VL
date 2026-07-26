"""``ms download`` command — fetch a single file or a full repo snapshot."""

from __future__ import annotations

import sys
from argparse import Action
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..api import HubApi
from ..constants import RepoType
from .base import CLICommand, add_repo_type_arg, info, make_api, success, warn
from .compat import (
    PatternAction,
    add_legacy_download_args,
    add_subcmd_token_endpoint,
    normalize_download_args,
    normalize_patterns,
)


def _resolve_cli_endpoint(endpoint: str | None) -> str | None:
    """Auto-complete bare domain names with ``https://``."""
    if not endpoint:
        return None
    endpoint = endpoint.strip().rstrip("/")
    if not endpoint:
        return None
    if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
        endpoint = f"https://{endpoint}"
    return endpoint


class DownloadCommand(CLICommand):
    """Download files or whole repositories from ModelScope Hub."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser(
            "download",
            help="Download a file or full snapshot of a repository.",
        )
        p.add_argument(
            "repo_id",
            nargs="?",
            default=None,
            help="Canonical 'owner/name' identifier.",
        )
        p.add_argument(
            "files",
            nargs="*",
            help="Optional list of file paths to download. Empty = full snapshot.",
        )
        add_repo_type_arg(
            p,
            choices=[RepoType.MODEL.value, RepoType.DATASET.value],
            default=RepoType.MODEL.value,
            required=False,
        )
        p.add_argument("--revision", default=None, help="Branch / tag / commit (default: master).")
        p.add_argument("--cache-dir", dest="cache_dir", default=None, help="Override cache directory.")
        p.add_argument("--local-dir", dest="local_dir", default=None,
                       help="Download directly to this directory (bypasses cache).")
        p.add_argument(
            "--max-workers",
            dest="max_workers",
            type=int,
            default=4,
            help="Concurrency for full-repo snapshot downloads.",
        )
        p.add_argument(
            "--include",
            dest="allow_patterns",
            nargs="+",
            action=PatternAction,
            default=None,
            help="Glob to include (snapshot mode). Repeatable.",
        )
        p.add_argument(
            "--exclude",
            dest="ignore_patterns",
            nargs="+",
            action=PatternAction,
            default=None,
            help="Glob to exclude (snapshot mode). Repeatable.",
        )
        p.add_argument("--force", action="store_true", help="Re-download even if cached.")

        # Legacy compat (hidden from --help)
        add_legacy_download_args(p)
        add_subcmd_token_endpoint(p)

        p.set_defaults(_command=DownloadCommand)

    def execute(self) -> None:
        normalize_download_args(self.args)

        # Handle collection download separately
        if self.args.repo_type == "collection":
            self._download_collection()
            return

        api = self._make_api_with_endpoint()
        cache_dir: Path | None = Path(self.args.cache_dir) if self.args.cache_dir else None
        local_dir: Path | None = Path(self.args.local_dir) if self.args.local_dir else None

        if self.args.files:
            for file_path in self.args.files:
                local = api.download_file(
                    self.args.repo_id,
                    self.args.repo_type,
                    file_path,
                    revision=self.args.revision,
                    cache_dir=cache_dir,
                    local_dir=local_dir,
                    force=self.args.force,
                )
                success(f"{file_path} → {local}")
            return

        info(f"Downloading snapshot of {self.args.repo_id} ({self.args.repo_type})…")
        output = api.download_repo(
            self.args.repo_id,
            self.args.repo_type,
            revision=self.args.revision,
            cache_dir=cache_dir,
            local_dir=local_dir,
            allow_patterns=normalize_patterns(self.args.allow_patterns),
            ignore_patterns=normalize_patterns(self.args.ignore_patterns),
            max_workers=self.args.max_workers,
        )
        success(f"Snapshot ready at {output}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _make_api_with_endpoint(self) -> HubApi:
        """Build HubApi with resolved endpoint.

        Bare domains (e.g. ``modelscope.cn``) are auto-completed with
        ``https://``.  When no endpoint is provided, auto-detection via
        ``resolve_endpoint_for_read()`` is attempted.
        """
        endpoint = getattr(self.args, "endpoint", None)
        token = getattr(self.args, "token", None)

        if endpoint:
            endpoint = _resolve_cli_endpoint(endpoint)
            return HubApi(token=token, endpoint=endpoint)

        api = make_api(self.args)
        try:
            resolved = api.resolve_endpoint_for_read(
                self.args.repo_id, repo_type=self.args.repo_type,
            )
            return HubApi(token=token, endpoint=resolved)
        except Exception:
            return api

    def _download_collection(self) -> None:
        """Download all skills from a collection."""
        api = make_api(self.args)
        local_dir = self.args.local_dir
        collection_id = self.args.repo_id

        data = api.legacy.get_collection(collection_id)
        elements = data.get("CollectionElements", {}).get(
            "CollectionElementVoList", []
        )
        valid = [
            e for e in elements
            if e.get("ElementPath") and e.get("ElementName")
        ]
        if not valid:
            warn(f"No valid skill elements found in collection: {collection_id}")
            return

        info(f"Found {len(valid)} skill(s) in collection, downloading…")

        def _download_one(elem: dict) -> tuple[str, str | None, str | None]:
            skill_id = f"{elem['ElementPath']}/{elem['ElementName']}"
            skill_name = elem["ElementName"]
            skill_dir = str(Path(local_dir) / skill_name) if local_dir else None
            try:
                result = api.download_repo(
                    skill_id,
                    repo_type=RepoType.SKILL,
                    local_dir=skill_dir,
                )
                return skill_id, str(result), None
            except Exception as exc:
                return skill_id, None, str(exc)

        succeeded, failed = [], []
        with ThreadPoolExecutor(max_workers=self.args.max_workers) as executor:
            futures = {executor.submit(_download_one, e): e for e in valid}
            for future in as_completed(futures):
                sid, path, error = future.result()
                if error:
                    failed.append((sid, error))
                    warn(f"Failed to download skill {sid}: {error}")
                else:
                    succeeded.append((sid, path))
                    success(f"skill {sid} → {path}")

        info(
            f"Download complete: {len(succeeded)} succeeded, "
            f"{len(failed)} failed"
        )
        if failed:
            for sid, err in failed:
                warn(f"  {sid}: {err}")
            sys.exit(1)
