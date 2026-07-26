"""``ms deploy`` / ``ms stop`` / ``ms logs`` / ``ms settings`` commands.

These wrap the studio / MCP lifecycle and the studio / skill settings
endpoints exposed by :class:`HubApi`.
"""

from __future__ import annotations

import json
from argparse import Action

from ..constants import RepoType
from .base import (
    CLICommand,
    add_repo_type_arg,
    info,
    make_api,
    parse_kv_pairs,
    success,
)
from .compat import add_subcmd_token_endpoint


class DeployCommand(CLICommand):
    """Deploy a Studio space or an MCP server."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("deploy", help="Deploy a studio space or MCP server.")
        p.add_argument("repo_id")
        add_repo_type_arg(
            p,
            choices=[RepoType.STUDIO.value, RepoType.MCP.value],
            default=RepoType.STUDIO.value,
            required=False,
        )
        add_subcmd_token_endpoint(p)
        p.set_defaults(_command=DeployCommand)

    def execute(self) -> None:
        api = make_api(self.args)
        api.deploy_repo(self.args.repo_id, self.args.repo_type)
        success(f"Deploy requested for {self.args.repo_type}: {self.args.repo_id}")


class StopCommand(CLICommand):
    """Stop a running Studio or undeploy an MCP server."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("stop", help="Stop a studio space or undeploy MCP server.")
        p.add_argument("repo_id")
        add_repo_type_arg(
            p,
            choices=[RepoType.STUDIO.value, RepoType.MCP.value],
            default=RepoType.STUDIO.value,
            required=False,
        )
        add_subcmd_token_endpoint(p)
        p.set_defaults(_command=StopCommand)

    def execute(self) -> None:
        api = make_api(self.args)
        api.stop_repo(self.args.repo_id, self.args.repo_type)
        success(f"Stop requested for {self.args.repo_type}: {self.args.repo_id}")


class LogsCommand(CLICommand):
    """Stream paginated run / build logs of a Studio space."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("logs", help="Fetch logs for a studio space.")
        p.add_argument("repo_id")
        add_repo_type_arg(
            p,
            choices=[RepoType.STUDIO.value],
            default=RepoType.STUDIO.value,
            required=False,
        )
        p.add_argument("--log-type", dest="log_type", choices=["run", "build"], default="run")
        p.add_argument("--page", "--page-num", dest="page_num", type=int, default=1)
        p.add_argument("--page-size", dest="page_size", type=int, default=100)
        p.add_argument("--keyword", default=None)
        add_subcmd_token_endpoint(p)
        p.set_defaults(_command=LogsCommand)

    def execute(self) -> None:
        api = make_api(self.args)
        payload = api.get_repo_logs(
            self.args.repo_id,
            self.args.repo_type,
            log_type=self.args.log_type,
            page_num=self.args.page_num,
            page_size=self.args.page_size,
            keyword=self.args.keyword,
        )
        # Different backend shapes — we try common keys then fall back to JSON.
        lines = _extract_log_lines(payload)
        if lines:
            for line in lines:
                info(line)
        else:
            info(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


class SettingsCommand(CLICommand):
    """Update Studio / Skill settings via ``key=value`` tokens."""

    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser(
            "settings",
            help="Update studio or skill settings (key=value pairs).",
        )
        p.add_argument("repo_id")
        add_repo_type_arg(
            p,
            choices=[RepoType.STUDIO.value, RepoType.SKILL.value],
            default=RepoType.STUDIO.value,
            required=False,
        )
        p.add_argument("settings", nargs="+", help="One or more key=value pairs.")
        add_subcmd_token_endpoint(p)
        p.set_defaults(_command=SettingsCommand)

    def execute(self) -> None:
        kv = parse_kv_pairs(self.args.settings)
        api = make_api(self.args)
        api.update_repo_settings(self.args.repo_id, self.args.repo_type, **kv)
        success(f"Updated {len(kv)} setting(s) on {self.args.repo_id}.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_log_lines(payload: object) -> list[str]:
    """Best-effort extraction of log lines from various backend shapes."""
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict):
        for key in ("logs", "items", "list", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [str(v) if not isinstance(v, dict) else (v.get("message") or json.dumps(v, ensure_ascii=False)) for v in value]
            if isinstance(value, str):
                return value.splitlines()
    return []
