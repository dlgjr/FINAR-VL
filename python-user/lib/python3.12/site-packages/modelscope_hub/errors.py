"""Exception hierarchy for the ModelScope Hub SDK.

Error codes follow the ModelScope global error-code specification
(``modelscope-errorcode`` registry).  Format: ``E{severity}{seq}``.

Severity layers::

    1 = Infrastructure (network, storage, timeout, rate-limiting, cache)
    2 = Data (file integrity, format, missing data)
    3 = Invocation (auth, permission, parameter validation, resource lookup)
    9 = Unknown / catch-all

The hierarchy is intentionally shallow and protocol-agnostic so callers can
catch broad categories (e.g. :class:`APIError`) without coupling to HTTP
status codes.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

if TYPE_CHECKING:  # pragma: no cover - type-only imports
    from requests import Response

# ---------------------------------------------------------------------------
# Credential redaction helpers
# ---------------------------------------------------------------------------
_SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "token", "secret", "password", "cookie", "authorization",
    "credential", "session", "api_key", "apikey",
)
_SENSITIVE_QUERY_KEYS: frozenset[str] = frozenset({
    "token", "access_token", "auth_token", "api_key", "apikey",
    "cookie", "m_session_id", "session",
    "secret", "password", "key", "authorization", "credentials",
})
_SENSITIVE_BODY_KEYS: re.Pattern[str] = re.compile(
    "|".join(_SENSITIVE_KEYWORDS), re.IGNORECASE,
)
_REDACTED = "***"


def _redact_url(url: str) -> str:
    """Strip sensitive query parameters from a URL."""
    try:
        parsed = urlparse(url)
    except Exception:
        return url
    if not parsed.query:
        return url
    params = parse_qs(parsed.query, keep_blank_values=True)
    clean_parts: list[str] = []
    for k, vals in params.items():
        if k.lower() in _SENSITIVE_QUERY_KEYS:
            clean_parts.append(f"{k}={_REDACTED}")
        else:
            for v in vals:
                clean_parts.append(f"{k}={v}")
    return urlunparse(parsed._replace(query="&".join(clean_parts)))


def _redact_body(body: Any) -> Any:
    """Deep-redact sensitive keys in a response body structure."""
    if isinstance(body, dict):
        return {
            k: _REDACTED if _SENSITIVE_BODY_KEYS.search(k) else _redact_body(v)
            for k, v in body.items()
        }
    if isinstance(body, list):
        return [_redact_body(item) for item in body]
    return body


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class HubError(Exception):
    """Base class for every error raised by :mod:`modelscope_hub`.

    Attributes
    ----------
    error_code : str | None
        ModelScope global error code (e.g. ``"E1020"``).
    retryable : bool
        Whether the caller should retry the operation.
    suggestion : str
        Human-readable remediation hint.
    """

    error_code: str | None = "E9001"
    retryable: bool = False
    suggestion: str = "Unexpected error. Please retry or report the issue."

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        prefix = f"[{self.error_code}] " if self.error_code else ""
        return f"{prefix}{self.message}"


# ---------------------------------------------------------------------------
# API errors (HTTP-layer)
# ---------------------------------------------------------------------------
class APIError(HubError):
    """Error returned by the ModelScope Hub HTTP API."""

    error_code = "E9001"
    retryable = False
    suggestion = "Unexpected API error. Please retry or report the issue."

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        response_body: Any | None = None,
        url: str | None = None,
        method: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id
        self.response_body = response_body
        self.url = url
        self.method = method

    def __str__(self) -> str:
        parts: list[str] = []
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        if self.status_code is not None:
            parts.append(f"[{self.status_code}]")
        parts.append(self.message)
        if self.request_id:
            parts.append(f"(request_id={self.request_id})")
        detail = self._format_body_detail()
        if detail:
            parts.append(f"| {detail}")
        headline = " ".join(parts)
        debug_lines: list[str] = []
        if self.url:
            debug_lines.append(f"  Request: {self.method or 'GET'} {_redact_url(self.url)}")
        if self.response_body is not None:
            body_str = str(_redact_body(self.response_body))
            if len(body_str) > 500:
                body_str = body_str[:500] + "..."
            debug_lines.append(f"  Response: {body_str}")
        if debug_lines:
            return headline + "\n" + "\n".join(debug_lines)
        return headline

    def _format_body_detail(self) -> str | None:
        """Extract additional detail from response_body not already in message."""
        if self.response_body is None:
            return None
        if isinstance(self.response_body, dict):
            safe_body = _redact_body(self.response_body)
            extras: list[str] = []
            code = safe_body.get("Code") or safe_body.get("code")
            if code is not None:
                extras.append(f"code={code}")
            for key in ("Data", "data", "detail", "Detail", "errors"):
                val = safe_body.get(key)
                if val is not None:
                    val_str = str(val)
                    if len(val_str) > 300:
                        val_str = val_str[:300] + "..."
                    extras.append(f"{key}={val_str}")
            if extras:
                return ", ".join(extras)
            return None
        if self.message.startswith("HTTP "):
            body_str = str(self.response_body)
            if len(body_str) > 500:
                body_str = body_str[:500] + "..."
            return f"body={body_str}"
        return None


# -- Auth / Permission (E3001, E3002) --------------------------------------
class AuthenticationError(APIError):
    """Raised on HTTP 401 -- missing or invalid credentials."""

    error_code = "E3001"
    retryable = False
    suggestion = "Authentication failed. Please verify your token is valid."


class PermissionDeniedError(APIError):
    """Raised on HTTP 403 -- authenticated but not authorised."""

    error_code = "E3002"
    retryable = False
    suggestion = "Permission denied. Please verify your access rights."


# -- Resource / Validation (E3020, E3021) -----------------------------------
class NotExistError(APIError):
    """Raised on HTTP 404 -- target resource does not exist."""

    error_code = "E3020"
    retryable = False
    suggestion = (
        "The requested resource does not exist, or it is private and requires "
        "authentication. Use `ms login` or pass --token to authenticate."
    )


class InvalidParameter(APIError, ValueError):
    """Raised on HTTP 400, or locally when caller-supplied arguments are invalid.

    Inherits :class:`ValueError` so existing ``except ValueError`` handlers
    continue to work during the transition period.
    """

    error_code = "E3021"
    retryable = False
    suggestion = "Invalid request parameters. Please check and retry."


class AlreadyExistsError(InvalidParameter):
    """Resource already exists (e.g., repo name is taken).

    Error code: E3026
    """

    error_code = "E3026"
    retryable = False
    suggestion = "Resource already exists. Use exist_ok=True to ignore."


# -- Rate limiting (E1021) --------------------------------------------------
class RateLimitError(APIError):
    """Raised on HTTP 429 -- client should back off and retry later."""

    error_code = "E1021"
    retryable = True
    suggestion = "Rate limit exceeded. Please reduce request frequency and retry."

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = 429,
        request_id: str | None = None,
        response_body: Any | None = None,
        url: str | None = None,
        method: str | None = None,
        retry_after: int | float | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            request_id=request_id,
            response_body=response_body,
            url=url,
            method=method,
        )
        self.retry_after = retry_after


# -- Server (E1002) ---------------------------------------------------------
class ServerError(APIError):
    """Raised on HTTP 5xx -- upstream service failure."""

    error_code = "E1002"
    retryable = True
    suggestion = "Server is currently unavailable. Please retry later."


# ---------------------------------------------------------------------------
# Non-HTTP errors
# ---------------------------------------------------------------------------
class NetworkError(HubError, ConnectionError):
    """Raised when the request could not reach the server (E1020).

    Also inherits :class:`ConnectionError` so existing
    ``except ConnectionError`` handlers continue to catch SDK network errors.
    """

    error_code = "E1020"
    retryable = True
    suggestion = "Unable to connect to the server. Please check your network."


class RequestTimeoutError(NetworkError, TimeoutError):
    """Raised when a request times out (E1001).

    Inherits :class:`NetworkError` so ``except NetworkError`` catches
    timeouts, and :class:`TimeoutError` so ``except TimeoutError`` catches
    them as well.
    """

    error_code = "E1001"
    retryable = True
    suggestion = "Request timed out. Please check your network and retry."


class StorageError(HubError):
    """Raised when blob storage operations (upload/download) fail (E1003)."""

    error_code = "E1003"
    retryable = True
    suggestion = (
        "File upload/download failed (storage service error). Please retry later."
    )


class FileIntegrityError(HubError):
    """Raised when a downloaded or uploaded file fails integrity validation (E2020)."""

    error_code = "E2020"
    retryable = True
    suggestion = "File SHA256 checksum mismatch. Will retry automatically."


# -- Cache errors (E1022) ---------------------------------------------------
class CacheError(HubError):
    """Base for local cache filesystem or metadata corruption."""

    error_code = "E1022"
    retryable = False
    suggestion = "Local cache directory error. Please check disk space and permissions."


class CacheNotFound(CacheError):
    """Cache directory does not exist or cannot be created."""

    def __init__(self, msg: str, cache_dir: str | None = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(msg, *args, **kwargs)
        self.cache_dir = cache_dir


class CorruptedCacheException(CacheError):
    """Unexpected structure in the ModelScope cache-system."""


# -- Operation not supported (E3023) ----------------------------------------
class NotSupportedError(HubError):
    """Raised when the requested operation is not supported in the current context."""

    error_code = "E3023"
    retryable = False
    suggestion = "This operation is not supported. Please check the documentation."


# ---------------------------------------------------------------------------
# Backward-compatible aliases
#
# The original names are preserved so that existing callers
# (e.g. ``except NotFoundError``) keep working.
# ---------------------------------------------------------------------------
NotFoundError = NotExistError
"""Alias: use :class:`NotExistError` instead."""

ValidationError = InvalidParameter
"""Alias: use :class:`InvalidParameter` instead."""

# Avoids shadowing the Python builtin ``PermissionError``.
PermissionError = PermissionDeniedError  # noqa: A001
"""Alias: use :class:`PermissionDeniedError` instead."""


# ---------------------------------------------------------------------------
# Status-code -> exception mapping
# ---------------------------------------------------------------------------
_STATUS_MAP: dict[int, type[APIError]] = {
    400: InvalidParameter,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotExistError,
    405: InvalidParameter,
    429: RateLimitError,
}


_CN_TO_EN: dict[str, str] = {
    "该名称已被注册使用，请重新命名": "Repository name already exists. Please choose a different name.",
    "用户未登录": "User not logged in.",
    "user not logged in": "User not logged in.",
    "更新模型失败": "Failed to update model.",
    "参数错误：版本名称不能为空": "Invalid parameter: tag name cannot be empty.",
    "模型不存在": "Model does not exist.",
    "数据集不存在": "Dataset does not exist.",
    "创建空间失败": "Failed to create studio.",
    "the current token no longer supports deletion operations. Please go to the site page : https://www.modelscope.cn to delete":
        "Deletion is restricted to web console. Visit https://modelscope.cn to delete.",
}


def _translate_message(msg: str) -> str:
    """Translate known Chinese server messages to English."""
    if not msg:
        return msg
    for cn, en in _CN_TO_EN.items():
        if cn in msg:
            return en
    return msg


def _extract_payload(response: "Response") -> tuple[str, str | None, Any | None]:
    """Best-effort extraction of (message, request_id, body) from a response."""
    request_id = response.headers.get("x-request-id") or response.headers.get("X-Request-Id")
    body: Any | None = None

    # Build a contextual fallback message that includes request method/path
    req = response.request
    if req and req.method and req.path_url:
        message = f"HTTP {response.status_code} on {req.method} {req.path_url}"
    else:
        message = f"HTTP {response.status_code}"

    try:
        body = response.json()
    except ValueError:
        body = response.text or None
        if isinstance(body, str) and body.strip():
            message = body.strip().splitlines()[0][:500]
        return _translate_message(message), request_id, body

    if isinstance(body, dict):
        for key in ("message", "Message", "msg", "Msg", "error", "Error", "detail", "Detail"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                message = value.strip()
                break
        request_id = (
            body.get("request_id") or body.get("requestId")
            or body.get("RequestId") or request_id
        )
    return _translate_message(message), request_id, body


def raise_for_status(response: "Response") -> None:
    """Inspect ``response`` and raise the most specific exception on failure.

    Parameters
    ----------
    response:
        A :class:`requests.Response` instance returned by the SDK transport.

    Raises
    ------
    APIError
        Or a subclass thereof when ``response.status_code`` indicates failure.
    """
    status = response.status_code
    if status < 400:
        return

    message, request_id, body = _extract_payload(response)

    # Extract request URL and method for debug context
    req = response.request
    url: str | None = response.url or (req.url if req else None)
    method: str | None = req.method if req else None

    if status >= 500:
        exc_cls: type[APIError] = ServerError
    else:
        exc_cls = _STATUS_MAP.get(status, APIError)

    # Detect "already exists" errors before falling back to InvalidParameter
    if exc_cls is InvalidParameter and isinstance(body, dict):
        code = body.get("Code") or body.get("code")
        msg_text = (body.get("Message") or body.get("message")
                    or body.get("msg") or body.get("Msg") or "").lower()
        is_exists = False
        if code is not None:
            try:
                if int(code) in _ALREADY_EXISTS_CODES:
                    is_exists = True
            except (TypeError, ValueError):
                pass
        if not is_exists:
            if any(kw in msg_text for kw in _ALREADY_EXISTS_KEYWORDS):
                is_exists = True
        if is_exists:
            exc_cls = AlreadyExistsError

    kwargs: dict[str, Any] = dict(
        status_code=status,
        request_id=request_id,
        response_body=body,
        url=url,
        method=method,
    )

    if exc_cls is RateLimitError:
        retry_after_raw = response.headers.get("Retry-After")
        retry_after: int | float | None = None
        if retry_after_raw:
            try:
                retry_after = int(retry_after_raw)
            except ValueError:
                try:
                    retry_after = float(retry_after_raw)
                except ValueError:
                    pass
        kwargs["retry_after"] = retry_after

    raise exc_cls(message, **kwargs)


# ---------------------------------------------------------------------------
# Repo-exists detection (shared by cli/repo.py and compat/hub_api.py)
# ---------------------------------------------------------------------------
_ALREADY_EXISTS_CODES: set[int] = {
    10020101001,   # 国内站 - 数据集已存在
    10010101001,   # 国内站 - 模型已存在
    10010202004,   # 国际站 - 名称已被使用
}

_ALREADY_EXISTS_KEYWORDS: frozenset[str] = frozenset({
    "exist",
    "already",
    "can not be used",
    "not available",
    "已被注册",
    "已存在",
    "名称不可用",
})


def is_repo_exists_error(exc: BaseException) -> bool:
    """Detect "repo already exists" errors.

    With the introduction of :class:`AlreadyExistsError`, this is now
    primarily a simple ``isinstance`` check. The keyword/code fallback
    is retained for backward compatibility with legacy exceptions that
    pre-date the structured error hierarchy.
    """
    if isinstance(exc, AlreadyExistsError):
        return True
    # Fallback: legacy exceptions that may not be AlreadyExistsError
    msg = str(exc).lower()
    if any(kw in msg for kw in _ALREADY_EXISTS_KEYWORDS):
        return True
    body = getattr(exc, "response_body", None)
    if isinstance(body, dict):
        code = body.get("Code") or body.get("code")
        try:
            if int(code) in _ALREADY_EXISTS_CODES:
                return True
        except (TypeError, ValueError):
            pass
    return False


__all__ = [
    # Base
    "APIError",
    "HubError",
    # Auth / Permission
    "AuthenticationError",
    "PermissionDeniedError",
    # Resource / Validation
    "NotExistError",
    "InvalidParameter",
    "AlreadyExistsError",
    # Rate limiting / Server
    "RateLimitError",
    "ServerError",
    # Non-HTTP
    "CacheError",
    "CacheNotFound",
    "CorruptedCacheException",
    "FileIntegrityError",
    "NetworkError",
    "RequestTimeoutError",
    "StorageError",
    # Operation support
    "NotSupportedError",
    # Backward-compatible aliases
    "NotFoundError",
    "PermissionError",
    "ValidationError",
    # Utilities
    "is_repo_exists_error",
    "raise_for_status",
]
