"""
Portfolio excerpt, adapted.

Instagram Graph API implementation of the SocialMediaProvider interface.
https://developers.facebook.com/docs/instagram-api/

Publishing takes two calls Meta forces on us: create a media container, poll it
until processing finishes, then publish by container id. You cannot publish in
one shot.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from dataclasses import dataclass
from enum import Enum


class MediaType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


@dataclass
class PublishResult:
    success: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


logger = logging.getLogger(__name__)


class InstagramProvider:
    """Instagram provider backed by the Graph API.

    Needs a Meta app with Instagram API access and a long-lived token.
    Credentials come in per request and are never persisted.

        config = {
            "account_id": "<ig-business-account-id>",
            "access_token": "<long-lived-token>",
            "graph_api_version": "v21.0",
        }
        provider = InstagramProvider(config)
        result = provider.publish_post(image_url="https://.../photo.jpg", caption="#x")
    """

    def __init__(self, config):
        # accept either a dict or a config object with the same attributes
        if isinstance(config, dict):
            self.account_id = config["account_id"]
            self.access_token = config["access_token"]
            self.api_version = config.get("graph_api_version", "v21.0")
        else:
            self.account_id = config.account_id
            self.access_token = config.access_token
            self.api_version = config.graph_api_version

        self._base_url = f"https://graph.facebook.com/{self.api_version}"
        self._timeout = 30
        self._retry_attempts = 3
        self._retry_delay = 5

    @property
    def name(self) -> str:
        return "instagram"

    @property
    def supported_media_types(self) -> List[MediaType]:
        return [MediaType.IMAGE, MediaType.VIDEO, MediaType.CAROUSEL,
                MediaType.STORY, MediaType.REEL]

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """Call the Graph API, retrying transient failures with a fixed backoff."""
        url = f"{self._base_url}/{endpoint}"
        params = dict(params or {})
        params["access_token"] = self.access_token

        for attempt in range(self._retry_attempts if retry else 1):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, params=params, timeout=self._timeout)
                elif method.upper() == "POST":
                    response = requests.post(url, params=params, data=data, timeout=self._timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(
                    "Request failed (attempt %d/%d): %s",
                    attempt + 1, self._retry_attempts, e,
                )
                if attempt < self._retry_attempts - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise

    def publish_post(self, image_url: str, caption: str = "", **options) -> PublishResult:
        """Run the container/poll/publish sequence and return the result."""
        try:
            container_params = {"image_url": image_url, "caption": caption}
            if "location_id" in options:
                container_params["location_id"] = options["location_id"]

            logger.info("Creating media container for: %s...", image_url[:50])
            container = self._make_request(
                "POST", f"{self.account_id}/media", params=container_params
            )
            creation_id = container.get("id")
            if not creation_id:
                return PublishResult(False, error="Failed to create media container",
                                     raw_response=container)

            self._wait_for_container(creation_id)

            logger.info("Publishing media...")
            published = self._make_request(
                "POST", f"{self.account_id}/media_publish",
                params={"creation_id": creation_id},
            )
            post_id = published.get("id")
            if not post_id:
                return PublishResult(False, error="Failed to publish media",
                                     raw_response=published)

            logger.info("Successfully published to Instagram: %s", post_id)
            return PublishResult(
                True, post_id=post_id,
                url=self._get_post_permalink(post_id), raw_response=published,
            )

        except Exception as e:
            logger.error("Failed to publish post: %s", e)
            return PublishResult(False, error=str(e))

    def _wait_for_container(
        self, container_id: str, max_wait: int = 60, check_interval: int = 5
    ) -> bool:
        """Poll the container until it reports FINISHED, ERROR, or max_wait elapses."""
        start = time.time()
        while time.time() - start < max_wait:
            try:
                response = self._make_request(
                    "GET", container_id, params={"fields": "status_code"}, retry=False
                )
                status = response.get("status_code")
                if status == "FINISHED":
                    return True
                if status == "ERROR":
                    logger.error("Container processing failed: %s", response)
                    return False
                logger.debug("Container status: %s, waiting...", status)
                time.sleep(check_interval)
            except Exception as e:
                logger.warning("Error checking container status: %s", e)
                time.sleep(check_interval)

        # images usually finish well under max_wait; publish anyway and let
        # media_publish surface the error if it really wasn't ready
        logger.warning("Container not ready after %ds, proceeding anyway", max_wait)
        return True

    def _get_post_permalink(self, post_id: str) -> Optional[str]:
        """Return the post's permalink, or None if the lookup fails."""
        try:
            response = self._make_request(
                "GET", post_id, params={"fields": "permalink"}
            )
            return response.get("permalink")
        except Exception:
            return None

    def get_profile_info(self) -> Dict[str, Any]:
        """Fetch the account's profile fields."""
        return self._make_request(
            "GET", self.account_id,
            params={"fields": "id,username,name,followers_count,media_count"},
        )

    def delete_post(self, post_id: str) -> bool:
        """Always return False. The Graph API exposes no delete; do it in the app."""
        logger.warning(
            "Instagram Graph API does not support post deletion. "
            "Please delete the post manually through the app."
        )
        return False

    def validate_credentials(self) -> bool:
        """Return True if the token can fetch the profile."""
        try:
            profile = self.get_profile_info()
            if "id" in profile:
                logger.info("Credentials valid for: @%s", profile.get("username", "unknown"))
                return True
            return False
        except Exception as e:
            logger.error("Credential validation failed: %s", e)
            return False
