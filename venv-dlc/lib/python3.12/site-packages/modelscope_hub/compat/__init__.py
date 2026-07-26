"""Backward-compatibility shims for the legacy ``modelscope.hub`` API surface.

This module provides drop-in replacements for commonly imported symbols from
the old ``modelscope.hub`` package.  Each function/class accepts the legacy
parameter signatures and delegates to the new ``modelscope_hub`` implementation.

Usage in the old SDK::

    # modelscope/hub/snapshot_download.py
    from modelscope_hub.compat import snapshot_download, dataset_snapshot_download

    # modelscope/hub/file_download.py
    from modelscope_hub.compat import model_file_download, dataset_file_download

    # modelscope/hub/api.py
    from modelscope_hub.compat import LegacyHubApi as HubApi
"""

from .constants import (
    DEFAULT_DATASET_REVISION,
    DEFAULT_MAX_WORKERS,
    FILE_HASH,
    MODELSCOPE_DOMAIN,
    MODELSCOPE_PREFER_AI_SITE,
    ModelVisibility_INTERNAL,
    ModelVisibility_PRIVATE,
    ModelVisibility_PUBLIC,
    REPO_TYPE_DATASET,
    REPO_TYPE_MODEL,
    REPO_TYPE_STUDIO,
    REPO_TYPE_SUPPORT,
    TEMPORARY_FOLDER_NAME,
)
from .file_download import dataset_file_download, model_file_download
from .hub_api import LegacyHubApi
from .snapshot_download import dataset_snapshot_download, snapshot_download

__all__ = [
    "LegacyHubApi",
    "dataset_file_download",
    "dataset_snapshot_download",
    "model_file_download",
    "snapshot_download",
    "DEFAULT_DATASET_REVISION",
    "DEFAULT_MAX_WORKERS",
    "FILE_HASH",
    "MODELSCOPE_DOMAIN",
    "MODELSCOPE_PREFER_AI_SITE",
    "ModelVisibility_INTERNAL",
    "ModelVisibility_PRIVATE",
    "ModelVisibility_PUBLIC",
    "REPO_TYPE_DATASET",
    "REPO_TYPE_MODEL",
    "REPO_TYPE_STUDIO",
    "REPO_TYPE_SUPPORT",
    "TEMPORARY_FOLDER_NAME",
]
