"""Repository management commands: create / info / list / delete.

These are registered as top-level commands (``ms create``, ``ms info``, etc.).
The legacy ``ms repo <action>`` form is preserved as a hidden alias.
"""

from __future__ import annotations

import argparse
from argparse import Action
from pathlib import Path

from ..constants import RepoType
from ..errors import AlreadyExistsError, is_repo_exists_error
from ..types import RepoInfo
from .base import CLICommand, add_repo_type_arg, error, info, make_api, print_env_table, render_table, success
from .compat import add_subcmd_token_endpoint


def _format_visibility(value: object) -> str:
    if value is None:
        return "-"
    return getattr(value, "label", None) or getattr(value, "name", None) or str(value)


def _print_repo_info(repo: RepoInfo) -> None:
    info(f"id         : {repo.id if repo.id is not None else '-'}")
    info(f"repo_id    : {repo.repo_id or '-'}")
    info(f"repo_type  : {getattr(repo.repo_type, 'value', repo.repo_type) or '-'}")
    info(f"visibility : {_format_visibility(repo.visibility)}")
    info(f"license    : {repo.license or '-'}")
    info(f"downloads  : {repo.downloads}")
    info(f"likes      : {repo.likes}")
    if repo.description:
        info(f"description: {repo.description}")
    if repo.tags:
        info(f"tags       : {', '.join(repo.tags)}")


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------
class CreateCommand(CLICommand):
    """``ms create`` — create a new repository."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("create", help="Create a new repository.")
        CreateCommand._add_arguments(p)
        p.set_defaults(_command=CreateCommand)

    @staticmethod
    def _add_arguments(p) -> None:
        p.add_argument("repo_id", help="Canonical 'owner/name' identifier.")
        add_repo_type_arg(p, choices=["model", "dataset", "studio", "skill"])
        p.add_argument("--visibility", choices=["public", "private", "internal"], default=None)
        p.add_argument("--license", dest="license", default=None)
        p.add_argument("--chinese-name", "--chinese_name", dest="chinese_name", default=None)
        p.add_argument("--description", dest="description", default=None)
        p.add_argument("--exist-ok", "--exist_ok", dest="exist_ok",
                       action="store_true", default=False,
                       help="Do not error if repository already exists.")
        gated_group = p.add_mutually_exclusive_group()
        gated_group.add_argument(
            "--gated", dest="gated", action="store_true", default=None,
            help="Create a gated (application-required) repo. Implies private visibility.",
        )
        gated_group.add_argument(
            "--no-gated", dest="gated", action="store_false",
            help="Explicitly create a non-gated repo (default).",
        )
        p.add_argument(
            "--sdk-type",
            dest="sdk_type",
            choices=["gradio", "streamlit", "docker", "static"],
            default=None,
            help="Studio SDK type.",
        )
        p.add_argument("--sdk-version", dest="sdk_version", default=None, help="Studio SDK version.")
        p.add_argument("--base-image", dest="base_image", default=None, help="Studio base image.")
        p.add_argument("--cover-image", dest="cover_image", default=None, help="Studio cover image URL.")
        p.add_argument("--hardware", dest="hardware", default=None, help="Studio hardware spec.")
        p.add_argument(
            "--category", dest="category", default=None,
            help="Skill category (required for skill repos). Options: "
                 "skill-management, developer-tools, marketing-seo, "
                 "frontend-development, ai-media, code-quality-testing, "
                 "mobile-development, cloud-devops, other.",
        )
        p.add_argument(
            "--skill-file", dest="skill_file", default=None,
            help="Local zip for skill (max 5 MB, root must contain exactly one "
                 "SKILL.md with YAML front-matter: name, version, description).",
        )
        add_subcmd_token_endpoint(p)

    def execute(self) -> None:
        api = make_api(self.args)
        extra: dict[str, object] = {}
        for key in ("sdk_type", "sdk_version", "base_image", "cover_image", "hardware", "category"):
            value = getattr(self.args, key, None)
            if value is not None:
                extra[key] = value

        skill_file = getattr(self.args, "skill_file", None)
        if skill_file:
            p = Path(skill_file).expanduser()
            if not p.exists():
                error(f"Skill file not found: {p}")
                raise SystemExit(2)
            info(f"Uploading skill file: {p}")
            file_id = api.upload_file_to_openapi(p)
            extra["skill_file"] = file_id

        visibility = self.args.visibility
        gated_mode = getattr(self.args, "gated", None)

        try:
            repo = api.create_repo(
                self.args.repo_id,
                self.args.repo_type,
                visibility=visibility,
                license=self.args.license,
                chinese_name=self.args.chinese_name,
                description=getattr(self.args, "description", None),
                gated_mode=gated_mode,
                **extra,
            )
            success(f"Created {self.args.repo_type}: {repo.repo_id or self.args.repo_id}")
        except AlreadyExistsError:
            if getattr(self.args, "exist_ok", False):
                info(f"Repository already exists: {self.args.repo_id}")
                return
            raise
        except Exception as exc:
            if getattr(self.args, "exist_ok", False) and is_repo_exists_error(exc):
                info(f"Repository already exists: {self.args.repo_id}")
                return
            raise


class InfoCommand(CLICommand):
    """``ms info`` — show metadata for a repository."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("info", help="Show metadata for a repository.")
        InfoCommand._add_arguments(p)
        p.set_defaults(_command=InfoCommand)

    @staticmethod
    def _add_arguments(p) -> None:
        p.add_argument("repo_id")
        add_repo_type_arg(p)
        add_subcmd_token_endpoint(p)

    def execute(self) -> None:
        api = make_api(self.args)
        repo = api.get_repo(self.args.repo_id, self.args.repo_type)
        _print_repo_info(repo)


class DeleteCommand(CLICommand):
    """``ms delete`` — delete a repository."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("delete", help="Delete a repository (model or dataset).")
        DeleteCommand._add_arguments(p)
        p.set_defaults(_command=DeleteCommand)

    @staticmethod
    def _add_arguments(p) -> None:
        p.add_argument("repo_id")
        add_repo_type_arg(p, choices=[RepoType.MODEL.value, RepoType.DATASET.value])
        p.add_argument("--yes", "-y", action="store_true", help="Skip the confirmation prompt.")
        add_subcmd_token_endpoint(p)

    def execute(self) -> None:
        if not self.args.yes:
            answer = input(
                f"Delete {self.args.repo_type} {self.args.repo_id!r}? This cannot be undone. [y/N] "
            ).strip().lower()
            if answer not in ("y", "yes"):
                info("Aborted.")
                return
        api = make_api(self.args)
        api.delete_repo(self.args.repo_id, self.args.repo_type)
        success(f"Deleted {self.args.repo_type}: {self.args.repo_id}")


class ListCommand(CLICommand):
    """``ms list`` — list repositories or environment variables."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("list", help="List repositories or show configurable env vars.")
        ListCommand._add_arguments(p)
        p.set_defaults(_command=ListCommand)

    @staticmethod
    def _add_arguments(p) -> None:
        p.add_argument(
            "--envs", action="store_true", default=False,
            help="Show all configurable environment variables and exit.",
        )
        add_repo_type_arg(
            p,
            required=False,
            default=None,
            choices=[
                RepoType.MODEL.value,
                RepoType.DATASET.value,
                RepoType.SKILL.value,
                RepoType.MCP.value,
            ],
        )
        p.add_argument("--owner", default=None)
        p.add_argument("--search", default=None, help=argparse.SUPPRESS)
        paging = p.add_mutually_exclusive_group()
        paging.add_argument("--all", dest="fetch_all", action="store_true", default=False,
                            help="Fetch all pages automatically.")
        paging.add_argument("--page", dest="page_number", type=int, default=1)
        p.add_argument("--page-size", dest="page_size", type=int, default=10)
        add_subcmd_token_endpoint(p)

    _MAX_PAGE_SIZE = 50

    def execute(self) -> None:
        if self.args.envs:
            print_env_table()
            return

        if not self.args.repo_type:
            error("--repo-type is required (unless using --envs).")
            raise SystemExit(2)

        api = make_api(self.args)

        if getattr(self.args, "fetch_all", False):
            all_items = self._fetch_all_pages(api)
            if not all_items:
                info("(no repositories found)")
                return
            self._render_table(all_items)
            info(f"\ntotal {len(all_items)} repos")
        else:
            result = api.list_repos(
                self.args.repo_type,
                owner=self.args.owner,
                search=self.args.search,
                page_number=self.args.page_number,
                page_size=self.args.page_size,
            )
            if not result.items:
                info("(no repositories found)")
                return
            self._render_table(result.items)
            info(
                f"\npage {result.page_number} / total {result.total_count} "
                f"(page_size={result.page_size})"
            )

    def _fetch_all_pages(self, api) -> list[RepoInfo]:
        page_size = min(self.args.page_size, self._MAX_PAGE_SIZE)
        all_items: list[RepoInfo] = []
        page_number = 1
        while True:
            result = api.list_repos(
                self.args.repo_type,
                owner=self.args.owner,
                search=self.args.search,
                page_number=page_number,
                page_size=page_size,
            )
            all_items.extend(result.items)
            if not result.has_next or not result.items:
                break
            page_number += 1
            if page_number * page_size > 3000:
                info(f"\n(stopped at page {page_number - 1}: server offset limit reached)")
                break
        return all_items

    @staticmethod
    def _render_table(items: list[RepoInfo]) -> None:
        rows = [
            (
                r.repo_id or "-",
                _format_visibility(r.visibility),
                r.downloads,
                r.likes,
                r.license or "-",
            )
            for r in items
        ]
        info(render_table(rows, headers=["repo_id", "visibility", "downloads", "likes", "license"]))


# ---------------------------------------------------------------------------
# Hidden backward-compat group: ``ms repo <action>``
# ---------------------------------------------------------------------------
class RepoCommand(CLICommand):
    """Hidden compat dispatcher for ``ms repo create/info/list/delete``."""

    @staticmethod
    def register(subparsers: Action) -> None:
        parser = subparsers.add_parser("repo")

        try:
            subparsers._choices_actions = [
                a for a in subparsers._choices_actions if a.dest != "repo"
            ]
        except AttributeError:
            pass
        sub = parser.add_subparsers(dest="repo_action", metavar="ACTION")
        sub.required = True

        # Re-register leaf commands under the "repo" group
        p = sub.add_parser("create", help="Create a new repository.")
        CreateCommand._add_arguments(p)
        p.set_defaults(_command=CreateCommand)

        p = sub.add_parser("info", help="Show metadata for a repository.")
        InfoCommand._add_arguments(p)
        p.set_defaults(_command=InfoCommand)

        p = sub.add_parser("delete", help="Delete a repository.")
        DeleteCommand._add_arguments(p)
        p.set_defaults(_command=DeleteCommand)

        p = sub.add_parser("list", help="List repositories.")
        ListCommand._add_arguments(p)
        p.set_defaults(_command=ListCommand)

        parser.set_defaults(_command=RepoCommand)

    def execute(self) -> None:
        pass  # pragma: no cover - argparse dispatches to leaf _command


# Backward-compat alias used by main.py's _CreateAlias
_RepoCreate = CreateCommand
