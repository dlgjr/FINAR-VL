"""Lightweight logging facade.

The SDK never installs handlers on the application root logger; it only
attaches a single :class:`~logging.StreamHandler` to its own namespace when
none is configured, and respects the ``MODELSCOPE_LOG_LEVEL`` environment
variable. This avoids the well-known "library hijacks logging" anti-pattern.
"""

from __future__ import annotations

import logging
import os
import threading

_ROOT_NAME = "modelscope_hub"
_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_ENV_LEVEL = "MODELSCOPE_LOG_LEVEL"

_lock = threading.Lock()
_configured = False


def _configure_root_logger() -> None:
    global _configured
    if _configured:
        return
    with _lock:
        if _configured:
            return
        logger = logging.getLogger(_ROOT_NAME)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
            logger.addHandler(handler)
            logger.propagate = False

        level_name = (os.environ.get(_ENV_LEVEL) or "INFO").upper()
        logger.setLevel(getattr(logging, level_name, logging.INFO))
        _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a namespaced logger under the ``modelscope_hub`` tree.

    Parameters
    ----------
    name:
        A child logger name. When omitted the root SDK logger is returned.
    """
    _configure_root_logger()
    if not name or name == _ROOT_NAME:
        return logging.getLogger(_ROOT_NAME)
    if name.startswith(f"{_ROOT_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_ROOT_NAME}.{name}")


__all__ = ["get_logger"]
