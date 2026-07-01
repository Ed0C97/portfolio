"""
Portfolio excerpt, adapted.

Provider contracts for storage and social media. The engine codes against these
ABCs, so swapping Cloudinary for S3 or Instagram for TikTok touches no call sites.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union


# =============================================================================
#                              DATA MODELS
# =============================================================================

class MediaType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


class UploadStatus(Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    UPLOADED = "uploaded"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class CloudFile:
    id: str
    name: str
    url: str
    public_url: str
    folder: str
    size: int
    format: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # providers hand back created_at as an ISO string; normalize to datetime
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class UploadResult:
    success: bool
    file: Optional[CloudFile] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class PublishResult:
    success: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


# =============================================================================
#                         CLOUD STORAGE PROVIDER
# =============================================================================

class CloudStorageProvider(ABC):
    """Storage backend contract (Cloudinary, S3, Azure Blob)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider key, e.g. 'cloudinary' or 's3'."""

    @abstractmethod
    def upload(
        self,
        file: Union[Path, BinaryIO, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        **options,
    ) -> UploadResult:
        """Upload from a path, file-like object, or raw bytes."""

    @abstractmethod
    def delete(self, file_id: str) -> bool:
        """Delete by provider file id."""

    @abstractmethod
    def list_files(
        self, folder: str = "", limit: int = 100, offset: int = 0
    ) -> List[CloudFile]:
        """List a folder, paginated."""

    @abstractmethod
    def get_public_url(self, file_id: str, **transform_options) -> str:
        """Public URL for a file; transform_options apply provider-side edits."""

    @abstractmethod
    def download(self, file_id: str, destination: Path) -> bool:
        """Download to a local path."""

    # --- default implementations subclasses may override ---------------------

    def folder_exists(self, folder: str) -> bool:
        # no native exists() across providers, so probe with a 1-item list
        try:
            self.list_files(folder, limit=1)
            return True
        except Exception:
            return False

    def delete_folder(self, folder: str, recursive: bool = False) -> bool:
        # non-recursive is a no-op: most stores treat folders as path prefixes,
        # so an empty prefix vanishes once its files are gone
        if recursive:
            for f in self.list_files(folder):
                self.delete(f.id)
        return True


# =============================================================================
#                         SOCIAL MEDIA PROVIDER
# =============================================================================

class SocialMediaProvider(ABC):
    """Publishing backend contract (Instagram, TikTok, Pinterest)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform key, e.g. 'instagram'."""

    @property
    @abstractmethod
    def supported_media_types(self) -> List[MediaType]:
        """Media types this platform accepts."""

    @abstractmethod
    def publish_post(self, image_url: str, caption: str = "", **options) -> PublishResult:
        """Publish a single post to the feed."""

    @abstractmethod
    def get_profile_info(self) -> Dict[str, Any]:
        """Return profile data (followers, post count, etc.)."""

    @abstractmethod
    def delete_post(self, post_id: str) -> bool:
        """Delete by post id."""

    # --- default implementations ---------------------------------------------

    def validate_credentials(self) -> bool:
        # cheapest authenticated call we can make; a 401 surfaces as False
        try:
            self.get_profile_info()
            return True
        except Exception:
            return False

    def publish_carousel(
        self, image_urls: List[str], caption: str = "", **options
    ) -> PublishResult:
        # not universal; subclasses that support albums override this
        raise NotImplementedError(f"{self.name} does not support carousel posts")

    def publish_reel(self, video_url: str, caption: str = "", **options) -> PublishResult:
        # not universal; subclasses that support short video override this
        raise NotImplementedError(f"{self.name} does not support reels")


# =============================================================================
#                          PROVIDER REGISTRY
# =============================================================================

class ProviderRegistry:
    """Holds the provider instances wired up at startup."""

    def __init__(self):
        self._storage: Dict[str, CloudStorageProvider] = {}
        self._social: Dict[str, SocialMediaProvider] = {}

    def register_storage(self, name: str, provider: CloudStorageProvider) -> None:
        self._storage[name] = provider

    def register_social(self, name: str, provider: SocialMediaProvider) -> None:
        self._social[name] = provider

    def get_storage(self, name: str) -> CloudStorageProvider:
        if name not in self._storage:
            raise KeyError(f"Storage provider '{name}' not registered")
        return self._storage[name]

    def get_social(self, name: str) -> SocialMediaProvider:
        if name not in self._social:
            raise KeyError(f"Social provider '{name}' not registered")
        return self._social[name]

    @property
    def storage_providers(self) -> List[str]:
        return list(self._storage.keys())

    @property
    def social_providers(self) -> List[str]:
        return list(self._social.keys())
