"""Base contracts and shared helpers for ``modelscope`` CLI subcommands.

Every concrete subcommand is a small, self-contained class that:

1. Registers its argparse parser via :meth:`CLICommand.register`.
2. Receives the parsed ``argparse.Namespace`` in its constructor.
3. Performs its work in :meth:`CLICommand.execute`.

This keeps :mod:`.main` free of subcommand-specific logic and makes adding
a new command a single-file change.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from argparse import Action, ArgumentParser, Namespace
from typing import Any, Iterable, Sequence

from ..api import HubApi
from ..constants import RepoType
from ..utils.format import tabulate as _tabulate


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------
class CLICommand(ABC):
    """Abstract contract every CLI subcommand implements."""

    def __init__(self, args: Namespace) -> None:
        self.args = args

    @staticmethod
    @abstractmethod
    def register(subparsers: Action) -> None:
        """Attach this command's argparse parser to ``subparsers``."""

    @abstractmethod
    def execute(self) -> None:
        """Run the command. Raise on failure; print on success."""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def make_api(args: Namespace) -> HubApi:
    """Construct a :class:`HubApi` honouring global and subcommand ``--token`` / ``--endpoint``.

    Automatically merges subcommand-level ``subcmd_token``/``subcmd_endpoint``
    into the namespace (subcommand values take precedence over global values).
    """
    subcmd_token = getattr(args, "subcmd_token", None)
    if subcmd_token:
        args.token = subcmd_token
    subcmd_endpoint = getattr(args, "subcmd_endpoint", None)
    if subcmd_endpoint:
        args.endpoint = subcmd_endpoint

    return HubApi(
        token=getattr(args, "token", None),
        endpoint=getattr(args, "endpoint", None),
    )


def add_repo_type_arg(
    parser: ArgumentParser,
    *,
    choices: Sequence[str] | None = None,
    default: str | None = None,
    required: bool = True,
    help: str = "Repository type.",
) -> None:
    """Attach a uniform ``--repo-type`` argument to ``parser``.

    Also accepts the legacy ``--repo_type`` (underscore) form for backward
    compatibility with the old ``modelscope`` CLI.
    """
    valid = list(choices) if choices else [t.value for t in RepoType]
    parser.add_argument(
        "--repo-type", "--repo_type",
        dest="repo_type",
        choices=valid,
        default=default,
        required=required and default is None,
        help=help,
    )


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------
def info(message: str) -> None:
    """Print a neutral status line."""
    print(message)


def success(message: str) -> None:
    """Print a success line (prefixed with ✓ when stdout is a TTY)."""
    prefix = "✓ " if sys.stdout.isatty() else ""
    print(f"{prefix}{message}")


def warn(message: str) -> None:
    """Print a warning line to stderr."""
    print(f"warning: {message}", file=sys.stderr)


def error(message: str) -> None:
    """Print an error line to stderr."""
    print(f"error: {message}", file=sys.stderr)


def render_table(rows: Iterable[Sequence[Any]], headers: Sequence[str]) -> str:
    """Format rows as a fixed-width text table."""
    return _tabulate(rows, headers)


def parse_kv_pairs(values: Iterable[str]) -> dict[str, str]:
    """Parse ``key=value`` argument tokens into a dict.

    Raises :class:`ValueError` when a token does not contain ``=``.
    """
    result: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(
                f"Invalid setting {raw!r}: expected 'key=value' format."
            )
        key, _, value = raw.partition("=")
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid setting {raw!r}: empty key.")
        result[key] = value
    return result


def print_env_table() -> None:
    """Print all configurable environment variables grouped by category."""
    import os
    from collections import defaultdict

    from ..constants import CATEGORY_ORDER, ENV_REGISTRY

    groups: dict[str, list] = defaultdict(list)
    for entry in ENV_REGISTRY:
        groups[entry.category].append(entry)

    for cat in CATEGORY_ORDER:
        entries = groups.get(cat)
        if not entries:
            continue
        info(f"\n[{cat}]")
        rows = []
        for e in entries:
            current = os.environ.get(e.name)
            deprecated_in_use = None
            if current is None and e.deprecated_names:
                for old in e.deprecated_names:
                    val = os.environ.get(old)
                    if val is not None:
                        current = val
                        deprecated_in_use = old
                        break
            display = current if current is not None else "(not set)"
            if deprecated_in_use:
                display += f"  (via deprecated {deprecated_in_use})"
            rows.append((e.name, display, e.default, e.description))
        info(render_table(rows, headers=["Variable", "Current", "Default", "Description"]))


__all__ = [
    "CLICommand",
    "add_repo_type_arg",
    "error",
    "info",
    "make_api",
    "parse_kv_pairs",
    "print_env_table",
    "render_table",
    "success",
    "warn",
]
