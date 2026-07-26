"""``ms secret`` group — manage Studio secrets."""

from __future__ import annotations

from argparse import Action

from ..constants import RepoType
from .base import CLICommand, add_repo_type_arg, info, make_api, render_table, success
from .compat import add_subcmd_token_endpoint


class SecretCommand(CLICommand):
    """Top-level dispatcher for the ``secret`` subcommands."""

    @staticmethod
    def register(subparsers: Action) -> None:
        parser = subparsers.add_parser("secret", help="Manage repository secrets (studio).")
        sub = parser.add_subparsers(dest="secret_action", metavar="ACTION")
        sub.required = True

        _SecretList.register(sub)
        _SecretAdd.register(sub)
        _SecretUpdate.register(sub)
        _SecretDelete.register(sub)

        parser.set_defaults(_command=SecretCommand)

    def execute(self) -> None:
        leaf = getattr(self.args, "_secret_leaf", None)
        if leaf is None:  # pragma: no cover
            raise SystemExit("No secret action given. See `ms secret --help`.")
        leaf(self.args).execute()


def _add_studio_repo_type(parser) -> None:
    add_repo_type_arg(
        parser,
        choices=[RepoType.STUDIO.value],
        default=RepoType.STUDIO.value,
        required=False,
    )


class _SecretList(CLICommand):
    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("list", help="List secrets of a studio space.")
        p.add_argument("repo_id")
        _add_studio_repo_type(p)
        add_subcmd_token_endpoint(p)
        p.set_defaults(_command=SecretCommand, _secret_leaf=_SecretList)

    def execute(self) -> None:
        api = make_api(self.args)
        secrets = api.list_secrets(self.args.repo_id, self.args.repo_type)
        if not secrets:
            info("(no secrets)")
            return
        rows = [
            (
                s.get("key") or s.get("name") or "-",
                s.get("description") or "-",
                s.get("created_at") or s.get("updated_at") or "-",
            )
            for s in secrets
        ]
        info(render_table(rows, headers=["key", "description", "updated_at"]))


class _SecretAdd(CLICommand):
    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("add", help="Add a new secret.")
        p.add_argument("repo_id")
        p.add_argument("key")
        p.add_argument("value")
        _add_studio_repo_type(p)
        add_subcmd_token_endpoint(p)
        p.set_defaults(_command=SecretCommand, _secret_leaf=_SecretAdd)

    def execute(self) -> None:
        api = make_api(self.args)
        api.add_secret(self.args.repo_id, self.args.key, self.args.value, self.args.repo_type)
        success(f"Added secret {self.args.key!r} to {self.args.repo_id}.")


class _SecretUpdate(CLICommand):
    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("update", help="Update an existing secret.")
        p.add_argument("repo_id")
        p.add_argument("key")
        p.add_argument("value")
        _add_studio_repo_type(p)
        add_subcmd_token_endpoint(p)
        p.set_defaults(_command=SecretCommand, _secret_leaf=_SecretUpdate)

    def execute(self) -> None:
        api = make_api(self.args)
        api.update_secret(self.args.repo_id, self.args.key, self.args.value, self.args.repo_type)
        success(f"Updated secret {self.args.key!r} on {self.args.repo_id}.")


class _SecretDelete(CLICommand):
    @staticmethod
    def register(subparsers: Action) -> None:
        p = subparsers.add_parser("delete", help="Delete a secret.")
        p.add_argument("repo_id")
        p.add_argument("key")
        _add_studio_repo_type(p)
        p.add_argument("--yes", "-y", action="store_true")
        add_subcmd_token_endpoint(p)
        p.set_defaults(_command=SecretCommand, _secret_leaf=_SecretDelete)

    def execute(self) -> None:
        if not self.args.yes:
            answer = input(
                f"Delete secret {self.args.key!r} from {self.args.repo_id}? [y/N] "
            ).strip().lower()
            if answer not in ("y", "yes"):
                info("Aborted.")
                return
        api = make_api(self.args)
        api.delete_secret(self.args.repo_id, self.args.key, self.args.repo_type)
        success(f"Deleted secret {self.args.key!r} from {self.args.repo_id}.")
