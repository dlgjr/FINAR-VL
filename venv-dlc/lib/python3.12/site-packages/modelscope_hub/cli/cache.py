"""``ms cache`` group — scan and clear the local cache."""

from __future__ import annotations

import sys
from argparse import Action

from ..constants import RepoType
from ..utils.format import format_size
from .base import CLICommand, error, info, make_api, render_table, success, warn


class CacheCommand(CLICommand):
    """Top-level dispatcher for the ``cache`` subcommands."""

    @staticmethod
    def register(subparsers: Action) -> None:
        parser = subparsers.add_parser("cache", help="Inspect or clear the local cache.")
        sub = parser.add_subparsers(dest="cache_action", metavar="ACTION")
        sub.required = True

        _CacheScan.register(sub)
        _CacheClear.register(sub)
        _CacheVerify.register(sub)

        parser.set_defaults(_command=CacheCommand)

    def execute(self) -> None:
        leaf = getattr(self.args, "_cache_leaf", None)
        if leaf is None:  # pragma: no cover
            raise SystemExit("No cache action given. See `ms cache --help`.")
        leaf(self.args).execute()


def _human_size(num: int) -> str:
    """Format a byte count using IEC suffixes."""
    return format_size(num)


class _CacheScan(CLICommand):
    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("scan", help="Show cached repositories and disk usage.")
        p.add_argument("--cache-dir", dest="cache_dir", default=None)
        p.set_defaults(_command=CacheCommand, _cache_leaf=_CacheScan)

    def execute(self) -> None:
        api = make_api(self.args)
        report = api.scan_cache(self.args.cache_dir)
        info(f"cache_dir: {report.cache_dir or '-'}")
        info(f"total    : {_human_size(report.total_size)} across {report.total_repos} repo(s)")
        if not report.repos:
            return
        rows = [
            (
                r.repo_id or "-",
                getattr(r.repo_type, "value", r.repo_type) or "-",
                r.revision or "-",
                r.nb_files,
                _human_size(r.size_on_disk),
                r.local_path or "-",
            )
            for r in report.repos
        ]
        info("")
        info(
            render_table(
                rows,
                headers=["repo_id", "repo_type", "revision", "files", "size", "path"],
            )
        )


class _CacheClear(CLICommand):
    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("clear", help="Remove cached files.")
        p.add_argument("--cache-dir", dest="cache_dir", default=None)
        p.add_argument(
            "--repo-type",
            dest="repo_type",
            choices=[t.value for t in RepoType],
            default=None,
        )
        p.add_argument("--repo-id", dest="repo_id", default=None)
        p.add_argument("--yes", "-y", action="store_true", help="Skip the confirmation prompt.")
        p.set_defaults(_command=CacheCommand, _cache_leaf=_CacheClear)

    def execute(self) -> None:
        # Reject ambiguous "--repo-id without --repo-type" early so we never
        # accidentally fall through to the "clear everything" branch.
        if self.args.repo_id and not self.args.repo_type:
            print(
                "Error: --repo-type is required when using --repo-id",
                file=sys.stderr,
            )
            raise SystemExit(2)

        scope = self.args.repo_id or self.args.repo_type or "the entire cache"
        if not self.args.yes:
            answer = input(f"Clear {scope}? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                info("Aborted.")
                return
        api = make_api(self.args)
        freed = api.clear_cache(
            cache_dir=self.args.cache_dir,
            repo_type=self.args.repo_type,
            repo_id=self.args.repo_id,
        )
        success(f"Freed {_human_size(freed)} from cache.")


def _format_paths(paths: list[str], limit: int = 10) -> str:
    """Format a bounded path list for verification diagnostics."""
    details = ", ".join(paths[:limit])
    return details + ("..." if len(paths) > limit else "")


class _CacheVerify(CLICommand):
    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("verify", help="Verify local files against Hub SHA-256 checksums.")
        p.add_argument("repo_id", help="Repository id in owner/name form.")
        p.add_argument(
            "--repo-type",
            choices=[t.value for t in RepoType],
            default="model",
        )
        p.add_argument("--revision", default=None)
        location = p.add_mutually_exclusive_group()
        location.add_argument("--cache-dir", default=None)
        location.add_argument("--local-dir", default=None)
        p.add_argument("--fail-on-missing-files", action="store_true")
        p.add_argument("--fail-on-extra-files", action="store_true")
        p.set_defaults(_command=CacheCommand, _cache_leaf=_CacheVerify)

    def execute(self) -> None:
        api = make_api(self.args)
        result = api.verify_cache(
            self.args.repo_id,
            self.args.repo_type,
            revision=self.args.revision,
            cache_dir=self.args.cache_dir,
            local_dir=self.args.local_dir,
        )
        failed = bool(result.mismatches)
        for mismatch in result.mismatches:
            error(f"{mismatch.path}: expected {mismatch.expected} ({mismatch.algorithm}), got {mismatch.actual}")
        if result.missing_paths:
            message = f"{len(result.missing_paths)} remote file(s) are missing locally"
            details = _format_paths(result.missing_paths)
            if self.args.fail_on_missing_files:
                error(f"{message}: {details}")
                failed = True
            else:
                warn(f"{message}: {details}")
        if result.extra_paths:
            message = f"{len(result.extra_paths)} local file(s) are absent from the remote revision"
            details = _format_paths(result.extra_paths)
            if self.args.fail_on_extra_files:
                error(f"{message}: {details}")
                failed = True
            else:
                warn(f"{message}: {details}")
        if result.unverified_paths:
            warn(f"{len(result.unverified_paths)} file(s) have no SHA-256 metadata and were skipped")
        if failed:
            raise SystemExit(1)
        success(
            f"Verified {result.checked_count} file(s) for {self.args.repo_type} "
            f"'{self.args.repo_id}' at {result.verified_path}."
        )
