"""``ms upload`` command — upload a single file or a folder."""

from __future__ import annotations

import os
from argparse import Action
from pathlib import Path

from ..constants import RepoType
from .base import CLICommand, add_repo_type_arg, error, info, make_api, success
from .compat import PatternAction, add_subcmd_token_endpoint


class UploadCommand(CLICommand):
    """Upload a local path to a repository.

    The local path is auto-detected as a file or directory. ``path_in_repo``
    defaults to the basename for files, or to the repo root for folders.
    """

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser(
            "upload",
            help="Upload a file or folder to a repository.",
        )
        p.add_argument("repo_id", help="Canonical 'owner/name' identifier.")
        p.add_argument(
            "local_path",
            nargs="?",
            default=None,
            help="Local file or folder to upload (default: auto-detect from repo name).",
        )
        p.add_argument(
            "path_in_repo",
            nargs="?",
            default=None,
            help="Destination path inside the repo. Defaults to basename / root.",
        )
        add_repo_type_arg(
            p,
            choices=[RepoType.MODEL.value, RepoType.DATASET.value],
            default=RepoType.MODEL.value,
            required=False,
        )
        p.add_argument("--commit-message", dest="commit_message", default=None)
        p.add_argument("--commit-description", dest="commit_description", default=None,
                       help="Description for the generated commit.")
        p.add_argument("--revision", default=None, help="Target branch (default: master).")
        p.add_argument(
            "--include",
            dest="allow_patterns",
            nargs="+",
            action=PatternAction,
            default=None,
            help="Glob to include (folder mode). Repeatable.",
        )
        p.add_argument(
            "--exclude",
            dest="ignore_patterns",
            nargs="+",
            action=PatternAction,
            default=None,
            help="Glob to exclude (folder mode). Repeatable.",
        )
        p.add_argument(
            "--max-workers",
            dest="max_workers",
            type=int,
            default=None,
            help="Concurrency for folder uploads.",
        )
        cache_group = p.add_mutually_exclusive_group()
        cache_group.add_argument(
            "--use-cache",
            dest="use_cache",
            action="store_true",
            default=True,
            help="Use .ms_upload_cache for resumable folder uploads (default).",
        )
        cache_group.add_argument(
            "--no-cache",
            dest="use_cache",
            action="store_false",
            help="Disable upload cache / resume support.",
        )
        p.add_argument(
            "--disable-tqdm",
            dest="disable_tqdm",
            action="store_true",
            default=False,
            help="Disable progress bars.",
        )
        p.add_argument(
            "--sync",
            dest="sync_remote_repo",
            action="store_true",
            default=False,
            help="Delete remote files not present locally after upload (sync mode).",
        )

        # Legacy compat
        add_subcmd_token_endpoint(p)

        p.set_defaults(_command=UploadCommand)

    def execute(self) -> None:
        api = make_api(self.args)

        local_path, path_in_repo = self._resolve_paths()
        local = Path(local_path).expanduser()

        if not local.exists():
            error(f"'{local}' is not a valid local path")
            raise SystemExit(2)

        if local.is_file():
            path_in_repo = path_in_repo or local.name
            info(f"Uploading file {local} → {self.args.repo_id}:{path_in_repo}")
            api.upload_file(
                self.args.repo_id,
                self.args.repo_type,
                str(local),
                path_in_repo,
                commit_message=self.args.commit_message,
                commit_description=self.args.commit_description,
                revision=self.args.revision,
                disable_tqdm=self.args.disable_tqdm,
            )
            success("Upload complete.")
            return

        path_in_repo = path_in_repo or ""
        info(f"Uploading folder {local} → {self.args.repo_id}:{path_in_repo or '/'}")
        result = api.upload_folder(
            self.args.repo_id,
            self.args.repo_type,
            str(local),
            path_in_repo=path_in_repo,
            commit_message=self.args.commit_message,
            commit_description=self.args.commit_description,
            revision=self.args.revision,
            allow_patterns=self.args.allow_patterns,
            ignore_patterns=self.args.ignore_patterns,
            max_workers=self.args.max_workers,
            use_cache=self.args.use_cache,
            disable_tqdm=self.args.disable_tqdm,
            sync_remote_repo=self.args.sync_remote_repo,
        )
        if result is None:
            success("All files already committed, nothing to upload.")
        else:
            success("Folder upload complete.")

    def _resolve_paths(self) -> tuple[str, str | None]:
        """Resolve local_path and path_in_repo with legacy smart defaults."""
        local_path = self.args.local_path
        path_in_repo = self.args.path_in_repo
        repo_name = self.args.repo_id.split("/")[-1] if "/" in self.args.repo_id else ""

        if local_path is not None:
            return local_path, path_in_repo

        # Legacy behavior: no local_path given → infer from repo name
        if repo_name and os.path.isfile(repo_name):
            return repo_name, repo_name
        if repo_name and os.path.isdir(repo_name):
            return repo_name, "."
        # Default: current directory
        return ".", path_in_repo
