"""Legacy constant mappings for backward compatibility with modelscope SDK."""

from ..constants import RepoType, Visibility

REPO_TYPE_MODEL: str = RepoType.MODEL.value
REPO_TYPE_DATASET: str = RepoType.DATASET.value
REPO_TYPE_STUDIO: str = RepoType.STUDIO.value
REPO_TYPE_SUPPORT: list[str] = [REPO_TYPE_MODEL, REPO_TYPE_DATASET, REPO_TYPE_STUDIO]

DEFAULT_DATASET_REVISION: str = "master"
DEFAULT_MAX_WORKERS: int = 4

# Visibility integer constants matching the old SDK
ModelVisibility_PUBLIC: int = int(Visibility.PUBLIC)
ModelVisibility_PRIVATE: int = int(Visibility.PRIVATE)
ModelVisibility_INTERNAL: int = int(Visibility.INTERNAL)

# Env var name constants (old SDK imports these as string constants)
MODELSCOPE_DOMAIN: str = "MODELSCOPE_DOMAIN"
MODELSCOPE_PREFER_AI_SITE: str = "MODELSCOPE_PREFER_AI_SITE"

# API response field names
FILE_HASH: str = "Sha256"

# Download temp folder name
TEMPORARY_FOLDER_NAME: str = "._____temp"
