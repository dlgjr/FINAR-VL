# Copyright (c) Alibaba, Inc. and its affiliates.
"""Agent repository transport SDK for ModelScope Hub.

This package provides only the low-level HTTP client for agent repositories.
Framework-aware workspace management (frameworks, conversion, sync, watch,
backups) lives in **modelscope-agent** (``ms_agent.agent_hub``).

Public API
----------
- :class:`AgentApi` -- HTTP client for agent repository operations
  (download/commit/LFS/list/create/delete).
- :class:`RemoteFileInfo` -- metadata for a single remote file.
- :func:`is_lfs_file` -- decide whether a file must use the LFS upload path.
"""
from ._api import AgentApi, RemoteFileInfo, is_lfs_file

__all__ = [
    "AgentApi",
    "RemoteFileInfo",
    "is_lfs_file",
]
