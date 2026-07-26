"""Minimal Git CLI wrapper for repository operations.

This module provides thin wrappers around ``git`` subprocess calls,
used by :class:`~._repository.Repository` for clone/pull/push/lfs ops.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from .errors import HubError
from .utils.logger import get_logger

logger = get_logger("git")


class GitError(HubError):
    """Raised when a git subprocess exits with a non-zero code."""

    error_code = "E1024"
    retryable = False
    suggestion = "Git operation failed. Please check network and repo permissions."


_URL_RE = re.compile(r"https?://\S+")


def _redact_git_url(url: str) -> str:
    """Strip userinfo from a single URL using urlparse (handles `@` in creds)."""
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        return urlunparse(parsed._replace(netloc=f"***@{parsed.hostname}" + (f":{parsed.port}" if parsed.port else "")))
    return url


class GitCommand:
    """Minimal Git CLI wrapper for repository operations.

    All methods are static/class-level — no instance state is required.
    """

    _git_path: str = "git"

    @classmethod
    def set_git_path(cls, path: str) -> None:
        """Override the git binary path (e.g. for testing)."""
        cls._git_path = path

    # ------------------------------------------------------------------
    # Core subprocess runner
    # ------------------------------------------------------------------
    @staticmethod
    def _redact(text: str) -> str:
        """Strip embedded credentials from arbitrary text."""
        return _URL_RE.sub(lambda m: _redact_git_url(m.group()), text)

    @classmethod
    def _run(cls, *args: str, cwd: Path | str | None = None) -> subprocess.CompletedProcess[str]:
        """Execute a git command and return the CompletedProcess.

        Raises :class:`GitError` on non-zero exit (unless it's a benign warning).
        """
        cmd = [cls._git_path, *args]
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        logger.debug("git %s (cwd=%s)", cls._redact(" ".join(args)), cwd or ".")

        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            if "nothing to commit" in stdout:
                logger.debug("Nothing to commit — repo is up to date")
                return result
            detail = cls._redact(stderr or stdout)
            logger.error("git %s failed: %s", args[0], detail)
            raise GitError(f"git {args[0]} failed: {detail}")

        return result

    # ------------------------------------------------------------------
    # Public operations
    # ------------------------------------------------------------------
    @classmethod
    def clone(
        cls,
        url: str,
        target_dir: Path,
        branch: str | None = None,
        token: str | None = None,
        depth: int | None = None,
    ) -> None:
        """Clone a repository.

        Parameters
        ----------
        url:
            Remote repository URL.
        target_dir:
            Local directory to clone into.
        branch:
            Optional branch/tag to checkout.
        token:
            Optional OAuth2 token injected into the URL.
        depth:
            Shallow clone depth (``None`` for full clone).
        """
        auth_url = cls._inject_token(url, token)
        args: list[str] = ["clone"]
        if branch:
            args.extend(["--branch", branch])
        if depth:
            args.extend(["--depth", str(depth)])
        args.extend([auth_url, str(target_dir)])

        try:
            cls._run(*args)
        except GitError:
            # Clone may succeed but hook fails — check if .git exists
            if (target_dir / ".git").is_dir():
                logger.warning(
                    "Clone exited non-zero but repository exists at %s. "
                    "Likely caused by a post-clone hook.",
                    target_dir,
                )
            else:
                raise

    @classmethod
    def pull(cls, repo_dir: Path, remote: str = "origin", branch: str | None = None) -> None:
        """Pull latest changes from remote."""
        args = ["pull", remote]
        if branch:
            args.append(branch)
        cls._run(*args, cwd=repo_dir)

    @classmethod
    def push(cls, repo_dir: Path, remote: str = "origin", branch: str | None = None) -> None:
        """Push local commits to remote."""
        args = ["push", remote]
        if branch:
            args.append(branch)
        cls._run(*args, cwd=repo_dir)

    @classmethod
    def add(cls, repo_dir: Path, *paths: str) -> None:
        """Stage files for commit."""
        args = ["add", *(paths or ["."])]
        cls._run(*args, cwd=repo_dir)

    @classmethod
    def commit(cls, repo_dir: Path, message: str) -> None:
        """Create a commit with the given message."""
        cls._run("commit", "-m", message, cwd=repo_dir)

    @classmethod
    def lfs_install(cls, repo_dir: Path) -> None:
        """Run ``git lfs install`` in the repository."""
        cls._run("lfs", "install", "--force", cwd=repo_dir)

    @classmethod
    def lfs_track(cls, repo_dir: Path, pattern: str) -> None:
        """Track a pattern with Git LFS."""
        cls._run("lfs", "track", pattern, cwd=repo_dir)

    @classmethod
    def is_lfs_available(cls) -> bool:
        """Check if Git LFS is installed and available."""
        try:
            cls._run("lfs", "env")
            return True
        except (GitError, FileNotFoundError):
            return False

    @classmethod
    def set_remote_url(cls, repo_dir: Path, url: str, remote: str = "origin") -> None:
        """Update the remote URL."""
        cls._run("remote", "set-url", remote, url, cwd=repo_dir)

    @classmethod
    def get_remote_url(cls, repo_dir: Path, remote: str = "origin") -> str:
        """Get the current remote URL."""
        result = cls._run("remote", "get-url", remote, cwd=repo_dir)
        return result.stdout.strip()

    @classmethod
    def config(cls, repo_dir: Path, key: str, value: str) -> None:
        """Set a local git config value."""
        cls._run("config", key, value, cwd=repo_dir)

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _inject_token(url: str, token: str | None) -> str:
        """Inject an OAuth2 token into an HTTP(S) URL.

        Returns the URL unchanged for SSH URLs or when token is None.
        """
        if not token:
            return url
        if url.startswith("git@"):
            return url

        try:
            parsed = urlparse(url)
        except Exception:
            return url

        if parsed.scheme not in ("http", "https"):
            return url
        if parsed.username == "oauth2":
            return url  # Already injected

        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        netloc = f"oauth2:{token}@{host}"
        return urlunparse(parsed._replace(netloc=netloc))

    @staticmethod
    def strip_token_from_url(url: str) -> str:
        """Remove OAuth2 credentials from a URL for safe logging."""
        if not url or "//oauth2" not in url:
            return url
        try:
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if parsed.port:
                host = f"{host}:{parsed.port}"
            return urlunparse(parsed._replace(netloc=host))
        except Exception:
            return url
