"""
Portfolio excerpt, adapted.

CloudStorageProvider backed by Cloudinary. Uses the official SDK when it is
installed, otherwise falls back to signed direct HTTP calls. Credentials below
are placeholders.
https://cloudinary.com/documentation/python_integration
"""

import hashlib
import io
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import requests

# real package pulls these from providers.base; inlined to keep the excerpt standalone
from dataclasses import dataclass, field


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


@dataclass
class UploadResult:
    success: bool
    file: Optional[CloudFile] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    HAS_CLOUDINARY_SDK = True
except ImportError:
    HAS_CLOUDINARY_SDK = False

logger = logging.getLogger(__name__)


class CloudinaryProvider:
    """Cloud-storage provider backed by Cloudinary."""

    def __init__(self, config):
        if isinstance(config, dict):
            self.cloud_name = config["cloud_name"]
            self.api_key = config["api_key"]
            self.api_secret = config["api_secret"]
        else:
            self.cloud_name = config.cloud_name
            self.api_key = config.api_key
            self.api_secret = config.api_secret

        self._base_url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}"

        if HAS_CLOUDINARY_SDK:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                secure=True,
            )
            logger.debug("Cloudinary SDK configured")
        else:
            logger.debug("Cloudinary SDK not available, using direct API")

    @property
    def name(self) -> str:
        return "cloudinary"

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Sign params the way Cloudinary expects: SHA1 of sorted k=v pairs with the secret appended."""
        sorted_params = sorted(
            [(k, v) for k, v in params.items() if v is not None],
            key=lambda x: x[0],
        )
        string_to_sign = "&".join(f"{k}={v}" for k, v in sorted_params) + self.api_secret
        return hashlib.sha1(string_to_sign.encode()).hexdigest()

    def upload(
        self,
        file: Union[Path, BinaryIO, bytes, str],
        folder: str = "",
        filename: Optional[str] = None,
        **options,
    ) -> UploadResult:
        """Upload a file via the SDK if present, else the direct API."""
        try:
            if HAS_CLOUDINARY_SDK:
                return self._upload_with_sdk(file, folder, filename, **options)
            return self._upload_with_api(file, folder, filename, **options)
        except Exception as e:
            logger.error("Upload failed: %s", e)
            return UploadResult(success=False, error=str(e))

    def _upload_with_sdk(self, file, folder, filename, **options) -> UploadResult:
        upload_options = {
            "folder": folder,
            "resource_type": options.get("resource_type", "image"),
            "overwrite": options.get("overwrite", True),
            "unique_filename": filename is None,
        }
        if filename:
            upload_options["public_id"] = filename
        if "tags" in options:
            upload_options["tags"] = options["tags"]

        file_input = self._coerce_file_input(file, for_sdk=True)
        response = cloudinary.uploader.upload(file_input, **upload_options)
        cloud_file = self._response_to_cloudfile(response)
        logger.info("Uploaded to Cloudinary: %s", cloud_file.name)
        return UploadResult(success=True, file=cloud_file, raw_response=response)

    def _upload_with_api(self, file, folder, filename, **options) -> UploadResult:
        params = {
            "folder": folder,
            "timestamp": int(time.time()),
            "overwrite": "true" if options.get("overwrite", True) else "false",
        }
        if filename:
            params["public_id"] = filename

        # signature must cover the params before api_key is added
        params["signature"] = self._generate_signature(params)
        params["api_key"] = self.api_key

        files: Dict[str, Any] = {}
        coerced = self._coerce_file_input(file, for_sdk=False)
        if isinstance(coerced, str):  # a URL
            params["file"] = coerced
        else:
            files["file"] = coerced

        try:
            resource_type = options.get("resource_type", "image")
            url = f"{self._base_url}/{resource_type}/upload"
            response = requests.post(url, data=params, files=files or None)
            response.raise_for_status()
            result = response.json()
            cloud_file = self._response_to_cloudfile(result)
            logger.info("Uploaded to Cloudinary: %s", cloud_file.name)
            return UploadResult(success=True, file=cloud_file, raw_response=result)
        finally:
            # close the handle we opened in _coerce_file_input for a Path
            if isinstance(file, Path) and "file" in files:
                files["file"].close()

    @staticmethod
    def _coerce_file_input(file, *, for_sdk: bool):
        """Coerce Path/bytes/URL/file-like input into something uploadable."""
        if isinstance(file, Path):
            return str(file) if for_sdk else open(file, "rb")
        if isinstance(file, bytes):
            return io.BytesIO(file)
        if isinstance(file, str) and file.startswith(("http://", "https://")):
            return file  # remote URL: Cloudinary fetches it
        return file  # already a file-like object

    def _response_to_cloudfile(self, response: Dict[str, Any]) -> CloudFile:
        """Map a Cloudinary upload response to CloudFile, defaulting created_at to now() if unparseable."""
        created_at = response.get("created_at", "")
        if isinstance(created_at, str) and created_at:
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.now()
        else:
            created_at = datetime.now()

        return CloudFile(
            id=response.get("public_id", ""),
            name=response.get("original_filename", response.get("public_id", "")),
            url=response.get("url", ""),
            public_url=response.get("secure_url", response.get("url", "")),
            folder=response.get("folder", ""),
            size=response.get("bytes", 0),
            format=response.get("format", ""),
            created_at=created_at,
            metadata={
                "width": response.get("width"),
                "height": response.get("height"),
                "resource_type": response.get("resource_type"),
                "version": response.get("version"),
            },
        )

    def get_public_url(self, file_id: str, **transform_options) -> str:
        """Build a delivery URL, folding any of w/h/c/q/f transforms into the path."""
        base = f"https://res.cloudinary.com/{self.cloud_name}/image/upload"
        keys = {"width": "w", "height": "h", "crop": "c", "quality": "q", "format": "f"}
        transforms = [
            f"{prefix}_{transform_options[key]}"
            for key, prefix in keys.items()
            if key in transform_options
        ]
        if transforms:
            return f"{base}/{','.join(transforms)}/{file_id}"
        return f"{base}/{file_id}"

    def download(self, file_id: str, destination: Path) -> bool:
        """Stream the public URL to a local path; return False on any error."""
        try:
            response = requests.get(self.get_public_url(file_id), stream=True)
            response.raise_for_status()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Downloaded from Cloudinary: %s -> %s", file_id, destination)
            return True
        except Exception as e:
            logger.error("Download failed: %s", e)
            return False
