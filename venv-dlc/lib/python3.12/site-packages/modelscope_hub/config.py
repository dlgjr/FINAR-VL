"""Runtime configuration for the ModelScope Hub SDK.

Configuration values follow a clear precedence chain:

1. Explicit constructor argument
2. Process environment variable
3. Persisted file on disk (token only)
4. Sensible default

This separation keeps the SDK trivially testable: tests can supply a
:class:`HubConfig` instance with overrides and never touch real credentials.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from .constants import (
    CONFIG_DIR_NAME,
    COOKIES_FILE_NAME,
    CREDENTIALS_DIR_NAME,
    DEFAULT_CACHE_DIR_NAME,
    DEFAULT_ENDPOINT,
    ENV_CACHE,
    ENV_MODELSCOPE_DOMAIN,
    GIT_TOKEN_FILE_NAME,
    SESSION_FILE_NAME,
    USER_INFO_FILE_NAME,
)
from .errors import CacheError, InvalidParameter

# Environment variable names — kept module-level for discoverability.
ENV_ENDPOINT = "MODELSCOPE_ENDPOINT"
ENV_TOKEN = "MODELSCOPE_API_TOKEN"
ENV_HOME = "MODELSCOPE_HOME"


def _expand(path: str | os.PathLike[str]) -> Path:
    return Path(path).expanduser().resolve()


@dataclass(slots=True)
class HubConfig:
    """Centralised runtime configuration object.

    The dataclass form makes it cheap to copy/override in tests via
    :func:`dataclasses.replace`, and keeps fields explicit and discoverable.
    """

    endpoint: str | None = None  # type: ignore[assignment]  # sentinel; always str after __post_init__
    cache_dir: Path = field(
        default_factory=lambda: _expand(
            os.environ.get(ENV_CACHE) or Path.home() / ".cache" / DEFAULT_CACHE_DIR_NAME
        )
    )
    config_dir: Path = field(
        default_factory=lambda: _expand(
            os.environ.get(ENV_HOME) or Path.home() / CONFIG_DIR_NAME
        )
    )
    token: str | None = None
    _logged_out: bool = field(default=False, init=False, repr=False)
    _endpoint_overridden: bool = field(default=False, init=False, repr=False)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        # Precedence: explicit arg > MODELSCOPE_ENDPOINT > MODELSCOPE_DOMAIN > default
        if self.endpoint is not None:
            self._endpoint_overridden = True
        elif os.environ.get(ENV_ENDPOINT):
            self.endpoint = os.environ.get(ENV_ENDPOINT)
            self._endpoint_overridden = True
        else:
            domain = os.environ.get(ENV_MODELSCOPE_DOMAIN, "").strip()
            if domain:
                warnings.warn(
                    "Environment variable MODELSCOPE_DOMAIN is deprecated, "
                    "use MODELSCOPE_ENDPOINT instead.",
                    FutureWarning,
                    stacklevel=2,
                )
                if not domain.startswith("http://") and not domain.startswith("https://"):
                    domain = f"https://{domain}"
                self.endpoint = domain
                self._endpoint_overridden = True
            else:
                self.endpoint = DEFAULT_ENDPOINT
        # Ensure endpoint always has a scheme
        if self.endpoint and not self.endpoint.startswith(("http://", "https://")):
            self.endpoint = f"https://{self.endpoint}"
        self.endpoint = self.endpoint.rstrip("/")
        if self.token is None:
            self.token = os.environ.get(ENV_TOKEN) or self.load_token()

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    @property
    def credentials_dir(self) -> Path:
        return self.config_dir / CREDENTIALS_DIR_NAME

    def ensure_dirs(self) -> None:
        """Create the config and cache directories if they do not exist."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.credentials_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - filesystem dependent
            raise CacheError(f"Failed to create SDK directories: {exc}") from exc

    # ------------------------------------------------------------------
    # Token persistence
    # ------------------------------------------------------------------
    def save_token(self, token: str) -> None:
        """Persist token as ``m_session_id`` cookie in ``credentials/cookies``.

        Creates a :class:`~requests.cookies.RequestsCookieJar` with a 30-day
        expiry, matching the old SDK convention where the API token lives
        exclusively inside the pickled cookie jar.
        """
        if not token or not token.strip():
            raise InvalidParameter("token must be a non-empty string")

        import time
        from http.cookiejar import Cookie
        from requests.cookies import RequestsCookieJar
        from urllib.parse import urlparse

        token = token.strip()
        domain = urlparse(self.endpoint).hostname or "modelscope.cn"
        expires = int(time.time()) + 30 * 24 * 3600  # 30 days

        jar = RequestsCookieJar()
        jar.set_cookie(Cookie(
            version=0, name="m_session_id", value=token,
            port=None, port_specified=False,
            domain=domain, domain_specified=True, domain_initial_dot=False,
            path="/", path_specified=True,
            secure=False, expires=expires, discard=False,
            comment=None, comment_url=None, rest={}, rfc2109=False,
        ))
        self.save_cookies(jar)
        self.token = token
        self._logged_out = False

    def load_token(self) -> str | None:
        """Load the API token from ``~/.modelscope/credentials/cookies``.

        Reads the pickled cookie jar and extracts the ``m_session_id`` value.
        Returns ``None`` if:
        - no cookies file exists
        - the ``m_session_id`` cookie has expired
        - :meth:`clear_token` was called (explicit logout)
        """
        if self._logged_out:
            return None

        cookies = self.load_cookies()
        if cookies:
            for cookie in cookies:
                if cookie.name == "m_session_id":
                    return cookie.value
        return None

    def clear_token(self) -> None:
        """Remove persisted credentials (deletes ``credentials/cookies``)."""
        self.token = None
        self._logged_out = True
        path = self.credentials_dir / COOKIES_FILE_NAME
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Credentials persistence (compat with old modelscope SDK)
    # ------------------------------------------------------------------
    def save_cookies(self, cookies: object) -> None:
        """Pickle cookies to ``~/.modelscope/credentials/cookies``."""
        import pickle
        import stat

        self.ensure_dirs()
        path = self.credentials_dir / COOKIES_FILE_NAME
        with open(path, "wb") as f:
            pickle.dump(cookies, f)
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def load_cookies(self) -> object | None:
        """Load saved cookies, returning None if absent or expired."""
        import pickle

        path = self.credentials_dir / COOKIES_FILE_NAME
        if not path.is_file():
            return None
        try:
            with open(path, "rb") as f:
                cookies = pickle.load(f)
        except (OSError, pickle.UnpicklingError):
            return None
        if not cookies:
            return None
        for cookie in cookies:
            if cookie.name == "m_session_id" and cookie.is_expired():
                return None
        return cookies

    def save_user_info(self, username: str, email: str) -> None:
        """Save ``username:email`` to ``~/.modelscope/credentials/user``."""
        self.ensure_dirs()
        path = self.credentials_dir / USER_INFO_FILE_NAME
        path.write_text(f"{username}:{email}", encoding="utf-8")

    def save_git_token(self, git_token: str) -> None:
        """Save git token to ``~/.modelscope/credentials/git_token``."""
        import stat

        self.ensure_dirs()
        path = self.credentials_dir / GIT_TOKEN_FILE_NAME
        path.write_text(git_token, encoding="utf-8")
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def load_git_token(self) -> str | None:
        """Read git token from ``~/.modelscope/credentials/git_token``."""
        path = self.credentials_dir / GIT_TOKEN_FILE_NAME
        if path.is_file():
            try:
                return path.read_text(encoding="utf-8").strip() or None
            except OSError:
                return None
        return None

    def get_session_id(self) -> str:
        """Return a stable SDK session UUID, auto-generating if absent.

        The session ID is persisted to ``~/.modelscope/credentials/session``
        and included in the User-Agent header for telemetry.
        """
        import uuid as _uuid

        path = self.credentials_dir / SESSION_FILE_NAME
        if path.is_file():
            try:
                sid = path.read_text(encoding="utf-8").strip()
                if len(sid) == 32:
                    return sid
            except OSError:
                pass
        sid = _uuid.uuid4().hex
        self.ensure_dirs()
        path.write_text(sid, encoding="utf-8")
        return sid


# Singleton-style accessor — kept as a function so tests can monkeypatch it.
_default_config: HubConfig | None = None


def get_default_config() -> HubConfig:
    """Return the lazily-instantiated process-wide default configuration."""
    global _default_config
    if _default_config is None:
        _default_config = HubConfig()
    return _default_config


def set_default_config(config: HubConfig | None) -> None:
    """Override (or clear) the process-wide default configuration."""
    global _default_config
    _default_config = config


__all__ = [
    "ENV_CACHE",
    "ENV_ENDPOINT",
    "ENV_HOME",
    "ENV_TOKEN",
    "HubConfig",
    "get_default_config",
    "set_default_config",
]
