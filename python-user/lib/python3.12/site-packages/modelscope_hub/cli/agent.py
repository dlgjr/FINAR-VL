# Copyright (c) Alibaba, Inc. and its affiliates.
"""``ms agent`` command -- low-level raw file transfer for agent repositories.

This is the *slim* Hub CLI. It supports only ``download``/``upload``/``list``
for raw file transfer to and from remote agent repositories, with no framework
awareness.  Framework-aware operations (convert, watch/sync, status, backups,
restore, stop) live in **modelscope-agent** -- use ``ms-agent agent ...``.
"""

from __future__ import annotations

import base64
import sys
from argparse import Action, RawDescriptionHelpFormatter
from pathlib import Path

from ..agent import AgentApi, is_lfs_file
from ..constants import Visibility
from ..errors import APIError
from .base import CLICommand

_CONVERT_HINT = (
    "This command transfers raw files only. For framework-aware conversion, "
    "watch/sync, status, backups and restore, use the modelscope-agent CLI: "
    "`ms-agent agent ...`."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fail(message: str) -> int:
    print(f"Error: {message}", file=sys.stderr)
    return 1


def _api_error_message(e: APIError, action: str = "request") -> str:
    status = e.status_code or 0
    if status == 401:
        return "authentication failed. Please login again."
    if status == 403:
        return "permission denied. You do not have access to this resource."
    if status == 404:
        return "resource not found. Check the repository name and try again."
    if status >= 500:
        return "server encountered an issue. Please wait a moment and try again."
    return f"{action} failed (HTTP {status}: {e.message})"


def _resolve_repo(repo: str, username: str) -> tuple[str, str]:
    """Resolve ``repo`` into ``(group, name)``.

    - ``owner/name`` -> ``(owner, name)`` (username ignored)
    - ``name``       -> ``(username, name)``
    """
    if "/" in repo:
        owner, _, name = repo.partition("/")
        return owner, name
    return username, repo


# ---------------------------------------------------------------------------
# Command implementations (raw transfer, no framework logic)
# ---------------------------------------------------------------------------
def _cmd_list(owner, page_number, page_size, *, endpoint, token) -> int:
    """List remote agent repositories."""
    if not endpoint:
        return _fail("not logged in. Provide endpoint.")
    client = AgentApi(endpoint=endpoint, token=token or "")
    try:
        result = client.list_agents(
            owner=owner, page_number=page_number, page_size=page_size)
    except APIError as e:
        return _fail(_api_error_message(e, "list"))
    except Exception as e:
        return _fail(f"list failed: {e}")

    items = result.get("items") or []
    total = result.get("total_count", len(items))
    if not items:
        print("(no agent repositories found)")
        return 0

    headers = ["repo_id", "framework", "visibility", "updated"]
    rows = []
    for item in items:
        owner_name = item.get("Path") or item.get("path") or ""
        name = item.get("Name") or item.get("name") or ""
        repo_id = f"{owner_name}/{name}" if owner_name else name
        fw = item.get("Framework") or item.get("framework") or "-"
        vis = item.get("Visibility") or item.get("visibility") or "-"
        updated = item.get("LastUpdatedDate") or item.get("last_updated_date") or "-"
        if isinstance(updated, str) and "T" in updated:
            updated = updated.split("T")[0]
        rows.append((repo_id, fw, vis, updated))

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in col_widths]))
    for row in rows:
        print(fmt.format(*[str(v) for v in row]))
    print(f"\npage {page_number} / total {total} (page_size={page_size})")
    return 0


def _cmd_download(repo, local_dir, revision, *, endpoint, token, username) -> int:
    """Download all raw files of a remote repository to a local directory."""
    if not repo:
        return _fail("--repo is required (the remote repository name).")
    if not endpoint:
        return _fail("not logged in. Provide endpoint.")
    if "/" not in repo and not username:
        return _fail(
            f"--repo '{repo}' requires login to resolve owner. "
            f"Use 'owner/name' format or run 'ms login' first.")

    group, name = _resolve_repo(repo, username or "")
    client = AgentApi(endpoint=endpoint, token=token or "")
    try:
        if client.repo_info(group, name) is None:
            return _fail(f"repository {group}/{name} not found.")
        paths = client.list_repo_files(group, name, revision=revision)
    except APIError as e:
        return _fail(_api_error_message(e, "download"))
    except Exception as e:
        return _fail(f"download failed: {e}")
    if not paths:
        return _fail(f"repository {group}/{name} has no files.")

    dest = Path(local_dir).expanduser() if local_dir else Path.cwd() / name
    dest.mkdir(parents=True, exist_ok=True)
    total = len(paths)
    for i, rel in enumerate(paths, 1):
        print(f"  [{i}/{total}] downloading {rel}", flush=True)
        try:
            data = client.download_repo_file(
                group, name, rel, revision=revision, binary=True)
        except APIError as e:
            return _fail(_api_error_message(e, "download"))
        except Exception as e:
            return _fail(f"download failed for {rel}: {e}")
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    print(f"Downloaded {total} file(s) to {dest}")
    return 0


def _cmd_upload(repo, local_dir, revision, dry_run, *, endpoint, token, username,
                visibility="public") -> int:
    """Upload raw files from a local path to a remote repository."""
    if not repo:
        return _fail("--repo is required (the remote repository name).")

    src = Path(local_dir).expanduser() if local_dir else Path.cwd()
    if not src.exists():
        return _fail(f"local path not found: {src}")

    # Discover files as (rel_path, abs_path) pairs; contents are read on demand
    # below so we never hold every file in memory at once.
    entries: list[tuple[str, Path]] = []
    if src.is_file():
        entries.append((src.name, src))
    else:
        for fp in sorted(src.rglob("*")):
            if fp.is_file():
                entries.append((fp.relative_to(src).as_posix(), fp))
    if not entries:
        return _fail(f"no files found under {src}.")

    if dry_run:
        print(f"[dry-run] would upload {len(entries)} file(s) to '{repo}':")
        for rel, fp in sorted(entries):
            print(f"  {rel} ({fp.stat().st_size} B)")
        return 0

    if not endpoint or not token:
        return _fail("not logged in. Run 'ms login' first.")
    if "/" not in repo and not username:
        return _fail(
            f"--repo '{repo}' requires login to resolve owner. "
            f"Use 'owner/name' format or run 'ms login' first.")

    group, name = _resolve_repo(repo, username or "")
    client = AgentApi(endpoint=endpoint, token=token)
    try:
        if not client.check_repo(group, name):
            client.create_repo(group, name, visibility=visibility)
    except Exception as exc:
        print(f"warning: create_repo check failed ({exc}), proceeding anyway.",
              file=sys.stderr)

    # Normal files (< LFS threshold, non-LFS extension) are small by definition
    # and go in a single commit; LFS files are read one at a time to bound
    # memory when uploading large binaries.
    normal_actions: list[dict] = []
    lfs_entries: list[tuple[str, Path]] = []
    for rel, fp in sorted(entries):
        size = fp.stat().st_size
        if is_lfs_file(rel, size):
            lfs_entries.append((rel, fp))
        else:
            normal_actions.append({
                "action": "create",
                "path": rel,
                "type": "normal",
                "size": size,
                "sha256": "",
                "content": base64.b64encode(fp.read_bytes()).decode("ascii"),
                "encoding": "base64",
            })
    try:
        if normal_actions:
            client.commit_files(
                group, name, normal_actions, revision=revision,
                commit_message="upload normal files")
        for rel, fp in lfs_entries:
            client.upload_lfs_file(
                group, name, rel, fp.read_bytes(), action="create",
                revision=revision, commit_message=f"upload LFS {rel}")
    except APIError as e:
        return _fail(_api_error_message(e, "upload"))
    except Exception as e:
        return _fail(f"upload failed: {e}")

    print(f"Uploaded {len(entries)} file(s) to {group}/{name}")
    return 0


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------
class AgentCommand(CLICommand):
    """Raw agent-repository file transfer: download, upload, list."""

    @staticmethod
    def register(subparsers: Action) -> None:
        _epilog = (
            "subcommand arguments:\n"
            "  download  -r REPO [--local-dir DIR] [--revision REV]\n"
            "  upload    -r REPO [--local-dir DIR] [--revision REV] [--dry-run]\n"
            "  list      [--owner OWNER] [--page N] [--page-size N]\n"
            "\n"
            "note:\n"
            f"  {_CONVERT_HINT}\n"
            "\n"
            "examples:\n"
            "  ms agent download -r user/my-agent --local-dir ./my-agent\n"
            "  ms agent upload -r user/my-agent --local-dir ./my-agent\n"
            "  ms agent list --owner user\n"
        )
        agent_parser = subparsers.add_parser(
            "agent",
            help="Transfer raw agent repository files (download, upload, list).",
            description="Low-level raw file transfer for remote agent repositories. "
                        + _CONVERT_HINT,
            epilog=_epilog,
            formatter_class=RawDescriptionHelpFormatter,
        )
        agent_parser.set_defaults(_command=AgentCommand)
        agent_sub = agent_parser.add_subparsers(dest="agent_command", metavar="ACTION")
        agent_sub.required = True

        # ---- download ----
        p_download = agent_sub.add_parser(
            "download",
            help="Download raw agent files from a remote repository",
            formatter_class=RawDescriptionHelpFormatter,
            description="Download all files of a remote agent repository to a local directory.\n"
                        + _CONVERT_HINT,
        )
        p_download.add_argument(
            "-r", "--repo", required=True,
            help="Remote repo identifier, supports owner/name format (e.g. user/my-agent)")
        p_download.add_argument(
            "--local-dir", default=None,
            help="Destination directory (default: ./<repo-name> under CWD)")
        p_download.add_argument(
            "--revision", default="master", help="Repository revision (default: master)")

        # ---- upload ----
        p_upload = agent_sub.add_parser(
            "upload",
            help="Upload raw agent files to a remote repository",
            formatter_class=RawDescriptionHelpFormatter,
            description="Upload files from a local path to a remote agent repository.\n"
                        + _CONVERT_HINT,
        )
        p_upload.add_argument(
            "-r", "--repo", required=True,
            help="Remote repo identifier, supports owner/name format (e.g. user/my-agent)")
        p_upload.add_argument(
            "--local-dir", default=None,
            help="Source path (file or directory) to upload (default: CWD)")
        p_upload.add_argument(
            "--revision", default="master", help="Repository revision (default: master)")
        p_upload.add_argument(
            "--visibility",
            choices=[Visibility.PUBLIC.label, Visibility.PRIVATE.label],
            default=Visibility.PUBLIC.label,
            help="Visibility of the remote repo when created (default: public)")
        p_upload.add_argument(
            "--dry-run", action="store_true",
            help="List files that would be uploaded, without actually uploading")

        # ---- list ----
        p_list = agent_sub.add_parser(
            "list",
            help="List remote agent repositories",
            description="Query and display remote agent repositories with pagination.",
        )
        p_list.add_argument(
            "--owner", default=None,
            help="Filter by owner username or organization name")
        p_list.add_argument(
            "--page", dest="page_number", type=int, default=1,
            help="Page number for pagination (default: 1)")
        p_list.add_argument(
            "--page-size", dest="page_size", type=int, default=10,
            help="Number of items per page (default: 10)")

    def execute(self) -> None:
        args = self.args
        action = args.agent_command

        from ..config import HubConfig
        config = HubConfig(
            endpoint=getattr(args, "endpoint", None),
            token=getattr(args, "token", None),
        )
        token = config.token
        endpoint = config.endpoint

        # Resolve current username for repos given without an explicit owner.
        username = ""
        needs_user = (
            action == "upload"
            or (action == "download" and "/" not in getattr(args, "repo", ""))
        )
        if needs_user and token:
            from .._openapi import OpenAPIClient
            try:
                openapi = OpenAPIClient(config=config)
                user_data = openapi.get_current_user() or {}
                username = user_data.get("username") or user_data.get("Username") or ""
            except Exception:
                username = ""

        if action == "download":
            rc = _cmd_download(
                repo=args.repo,
                local_dir=args.local_dir,
                revision=args.revision,
                endpoint=endpoint,
                token=token,
                username=username,
            )
        elif action == "upload":
            rc = _cmd_upload(
                repo=args.repo,
                local_dir=args.local_dir,
                revision=args.revision,
                dry_run=args.dry_run,
                visibility=args.visibility,
                endpoint=endpoint,
                token=token,
                username=username,
            )
        elif action == "list":
            rc = _cmd_list(
                owner=args.owner,
                page_number=args.page_number,
                page_size=args.page_size,
                endpoint=endpoint,
                token=token,
            )
        else:
            print(f"Unknown agent action: {action}")
            rc = 1

        if rc != 0:
            raise SystemExit(rc)
