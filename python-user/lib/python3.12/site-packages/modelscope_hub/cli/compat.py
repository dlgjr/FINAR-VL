"""CLI backward-compatibility utilities.

Provides argument normalization, deprecation warnings, and custom argparse
actions that allow the CLI to accept both the new canonical argument style
and the legacy style from the old ``modelscope`` SDK.
"""

from __future__ import annotations

import os
import warnings
from argparse import SUPPRESS, Action, ArgumentParser, Namespace
from typing import Any, Sequence


# ---------------------------------------------------------------------------
# Deprecation infrastructure
# ---------------------------------------------------------------------------
_SUPPRESS_ENVVAR = "MODELSCOPE_NO_DEPRECATION_WARNINGS"
_SUPPRESS_ENVVAR_OLD = "MODELSCOPE_HUB_NO_DEPRECATION_WARNINGS"


def deprecated_arg(old: str, new: str) -> None:
    """Emit a DeprecationWarning for a renamed CLI argument."""
    if os.environ.get(_SUPPRESS_ENVVAR) or os.environ.get(_SUPPRESS_ENVVAR_OLD):
        return
    warnings.warn(
        f"'{old}' is deprecated and will be removed in a future version. "
        f"Use '{new}' instead.",
        DeprecationWarning,
        stacklevel=3,
    )


# ---------------------------------------------------------------------------
# Custom argparse Action: support both nargs and append semantics
# ---------------------------------------------------------------------------
class PatternAction(Action):
    """Argparse action that accumulates values from repeated or multi-value uses.

    Supports both:
      --include a b c          (nargs='+' multi-value)
      --include a --include b  (repeated single-value)

    Result is always a flat list.
    """

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[str],
        option_string: str | None = None,
    ) -> None:
        current: list[str] = getattr(namespace, self.dest, None) or []
        if isinstance(values, str):
            current.append(values)
        else:
            current.extend(values)
        setattr(namespace, self.dest, current)


# ---------------------------------------------------------------------------
# Argument registration helpers
# ---------------------------------------------------------------------------
def add_legacy_download_args(parser: ArgumentParser) -> None:
    """Register hidden legacy-style download arguments."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--model", type=str, default=None, help=SUPPRESS)
    group.add_argument("--dataset", type=str, default=None, help=SUPPRESS)
    group.add_argument("--collection", type=str, default=None, help=SUPPRESS)

    parser.add_argument("--local_dir", dest="local_dir_legacy", default=None, help=SUPPRESS)
    parser.add_argument("--cache_dir", dest="cache_dir_legacy", default=None, help=SUPPRESS)


def add_subcmd_token_endpoint(parser: ArgumentParser) -> None:
    """Register hidden per-subcommand --token/--endpoint (legacy compat)."""
    parser.add_argument("--token", dest="subcmd_token", default=None, help=SUPPRESS)
    parser.add_argument("--endpoint", dest="subcmd_endpoint", default=None, help=SUPPRESS)


# ---------------------------------------------------------------------------
# Argument normalization
# ---------------------------------------------------------------------------
def normalize_download_args(args: Namespace) -> Namespace:
    """Normalize legacy download arguments to the canonical internal form.

    Handles mapping of:
      --model/--dataset → repo_id + repo_type
      --local_dir (underscore) → local_dir
      --cache_dir (underscore) → cache_dir
      subcmd_token/subcmd_endpoint → token/endpoint
    """
    # --model / --dataset / --collection → repo_id + repo_type
    if getattr(args, "model", None):
        deprecated_arg("--model", "positional repo_id")
        if args.repo_id is not None:
            if not args.files:
                args.files = []
            args.files.insert(0, args.repo_id)
        args.repo_id = args.model
        args.repo_type = "model"
    elif getattr(args, "dataset", None):
        deprecated_arg("--dataset", "positional repo_id with --repo-type dataset")
        if args.repo_id is not None:
            if not args.files:
                args.files = []
            args.files.insert(0, args.repo_id)
        args.repo_id = args.dataset
        args.repo_type = "dataset"
    elif getattr(args, "collection", None):
        deprecated_arg("--collection", "positional repo_id with --repo-type collection")
        if args.repo_id is not None:
            if not args.files:
                args.files = []
            args.files.insert(0, args.repo_id)
        args.repo_id = args.collection
        args.repo_type = "collection"

    # --local_dir (underscore) → local_dir
    legacy_local = getattr(args, "local_dir_legacy", None)
    if legacy_local:
        deprecated_arg("--local_dir", "--local-dir")
        if not getattr(args, "local_dir", None):
            args.local_dir = legacy_local

    # --cache_dir (underscore) → cache_dir
    legacy_cache = getattr(args, "cache_dir_legacy", None)
    if legacy_cache:
        deprecated_arg("--cache_dir", "--cache-dir")
        if not getattr(args, "cache_dir", None):
            args.cache_dir = legacy_cache

    # Merge subcommand-level auth
    _merge_subcmd_auth(args)

    # Ensure files is always a list
    if not getattr(args, "files", None):
        args.files = []

    if not args.repo_id:
        raise ValueError(
            "repo_id is required. Provide it as a positional argument "
            "or via --model/--dataset."
        )

    return args


def normalize_patterns(value: Any) -> list[str] | None:
    """Flatten pattern values into a simple list.

    Handles output from both PatternAction and legacy nargs='*'.
    Also splits comma-separated values (matching old SDK's ``convert_patterns``).
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = [value]
    result: list[str] = []
    for item in value:
        if isinstance(item, list):
            for sub in item:
                result.extend(_split_commas(sub))
        else:
            result.extend(_split_commas(item))
    return result or None


def _split_commas(s: str) -> list[str]:
    """Split a string on commas and strip whitespace from each part."""
    if "," in s:
        return [part.strip() for part in s.split(",") if part.strip()]
    return [s.strip()] if s.strip() else []


def _merge_subcmd_auth(args: Namespace, *, warn: bool = True) -> None:
    """Merge subcommand-level --token/--endpoint into the namespace.

    Subcommand-level values take precedence over global values (they are
    more specific). When *warn* is True, a deprecation warning is emitted
    advising users to use the global form.

    Parameters
    ----------
    warn : bool
        Emit deprecation warnings. Set to False when called from alias
        adapters where subcommand-level auth is the expected interface.
    """
    subcmd_token = getattr(args, "subcmd_token", None)
    if subcmd_token:
        if warn:
            deprecated_arg("subcommand --token", "global --token (before subcommand)")
        args.token = subcmd_token

    subcmd_endpoint = getattr(args, "subcmd_endpoint", None)
    if subcmd_endpoint:
        if warn:
            deprecated_arg("subcommand --endpoint", "global --endpoint (before subcommand)")
        args.endpoint = subcmd_endpoint
