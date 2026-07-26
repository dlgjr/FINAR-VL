"""Local Git repository representation.

Wraps :class:`~._git.GitCommand` to provide a higher-level OOP interface
for cloning, pushing, and managing a local checkout tied to a ModelScope
Hub remote.
"""

from __future__ import annotations

from pathlib import Path

from ._git import GitCommand, GitError
from .constants import DEFAULT_ENDPOINT, RepoType
from .utils.file_utils import ensure_dir
from .utils.logger import get_logger

logger = get_logger("repository")

# URL template for Git access
_GIT_URL_TEMPLATE = "{endpoint}/{type}s/{repo_id}.git"


class Repository:
    """Local Git repository representation.

    Provides lifecycle management for a local checkout linked to a
    ModelScope Hub remote repository.
    """

    def __init__(
        self,
        repo_dir: Path | str,
        repo_url: str | None = None,
        repo_id: str | None = None,
        repo_type: str = RepoType.MODEL,
        token: str | None = None,
        endpoint: str = DEFAULT_ENDPOINT,
    ) -> None:
        """
        Parameters
        ----------
        repo_dir:
            Local directory for the repository checkout.
        repo_url:
            Explicit Git remote URL. If not provided, computed from
            repo_id + repo_type + endpoint.
        repo_id:
            Repository identifier (``owner/name``). Used to compute
            repo_url when it's not given directly.
        repo_type:
            Repository type (model, dataset, etc.).
        token:
            OAuth2 token for authenticated operations.
        endpoint:
            Hub endpoint for URL construction.
        """
        self._repo_dir = Path(repo_dir).resolve()
        self._token = token
        self._endpoint = endpoint.rstrip("/")
        self._repo_type = repo_type
        self._repo_id = repo_id

        if repo_url:
            self._repo_url = repo_url
        elif repo_id:
            segment = f"{repo_type}s" if not repo_type.endswith("s") else repo_type
            self._repo_url = f"{self._endpoint}/{segment}/{repo_id}.git"
        else:
            self._repo_url = ""

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def repo_dir(self) -> Path:
        """Absolute path to the local repository directory."""
        return self._repo_dir

    @property
    def git_url(self) -> str:
        """Remote Git URL (without embedded credentials)."""
        return self._repo_url

    @property
    def authenticated_url(self) -> str:
        """Remote Git URL with token injected for push/pull."""
        return GitCommand._inject_token(self._repo_url, self._token)

    @property
    def exists(self) -> bool:
        """Whether the local repo directory already contains a .git folder."""
        return (self._repo_dir / ".git").is_dir()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def clone(self, revision: str = "master", depth: int | None = None) -> None:
        """Clone the remote repository into :attr:`repo_dir`.

        Parameters
        ----------
        revision:
            Branch or tag to checkout after clone.
        depth:
            Shallow clone depth (None for full history).
        """
        if self.exists:
            logger.info("Repository already cloned at %s", self._repo_dir)
            return

        ensure_dir(self._repo_dir.parent)
        logger.info("Cloning %s → %s", GitCommand.strip_token_from_url(self._repo_url), self._repo_dir)

        GitCommand.clone(
            url=self._repo_url,
            target_dir=self._repo_dir,
            branch=revision,
            token=self._token,
            depth=depth,
        )

        # Install LFS in the cloned repo
        if GitCommand.is_lfs_available():
            GitCommand.lfs_install(self._repo_dir)

    def pull(self, branch: str | None = None) -> None:
        """Pull latest changes from the remote."""
        self._ensure_exists()
        self._configure_auth()
        GitCommand.pull(self._repo_dir, branch=branch)

    def push(self, commit_message: str, branch: str | None = None) -> None:
        """Stage all changes, commit, and push.

        Parameters
        ----------
        commit_message:
            Message for the commit.
        branch:
            Branch to push to (default: current branch).
        """
        self._ensure_exists()
        self._configure_auth()

        # Stage all changes
        GitCommand.add(self._repo_dir)

        # Commit (may be a no-op if nothing changed)
        try:
            GitCommand.commit(self._repo_dir, commit_message)
        except GitError as exc:
            if "nothing to commit" in str(exc).lower():
                logger.info("Nothing to commit")
                return
            raise

        # Push
        GitCommand.push(self._repo_dir, branch=branch)
        logger.info("Pushed to %s", GitCommand.strip_token_from_url(self._repo_url))

    def add_and_commit(self, message: str, paths: list[str] | None = None) -> None:
        """Stage specific paths (or all) and commit without pushing."""
        self._ensure_exists()
        if paths:
            GitCommand.add(self._repo_dir, *paths)
        else:
            GitCommand.add(self._repo_dir)

        try:
            GitCommand.commit(self._repo_dir, message)
        except GitError as exc:
            if "nothing to commit" in str(exc).lower():
                logger.info("Nothing to commit")
                return
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_exists(self) -> None:
        """Raise if the local repo doesn't exist."""
        if not self.exists:
            raise GitError(f"Repository not found at {self._repo_dir}. Call clone() first.")

    def _configure_auth(self) -> None:
        """Inject token into the remote URL for authenticated ops."""
        if not self._token:
            return
        auth_url = GitCommand._inject_token(self._repo_url, self._token)
        try:
            GitCommand.set_remote_url(self._repo_dir, auth_url)
        except GitError:
            logger.debug("Could not update remote URL for auth")
