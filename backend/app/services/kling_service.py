"""
Kling 3.0 API Integration
Professional video generation from images
"""

import httpx
import asyncio
from typing import Optional, Dict, Any
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class KlingService:
    """Service for Kling 3.0 video generation API"""

    def __init__(self):
        self.api_key = settings.kling_api_key
        self.base_url = settings.kling_api_base_url
        self.client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: int = 15,
        style: str = "realistic",
    ) -> Dict[str, Any]:
        """
        Generate video from image using Kling API

        Args:
            image_url: S3 URL of the input image
            prompt: Text description/script for the video
            duration: Video duration in seconds (15, 30, or 60)
            style: Visual style (realistic, cinematic, anime, etc)

        Returns:
            {"job_id": str, "webhook_url": str, "status": "submitted"}
        """

        if not self.api_key:
            # Return mock response for testing
            logger.warning("Kling API key not set - returning mock response")
            return {
                "job_id": f"mock-job-{duration}",
                "status": "submitted",
                "webhook_url": None,
            }

        try:
            client = await self._get_client()

            payload = {
                "model": "kling-3.0",
                "input": {
                    "image_url": image_url,
                    "prompt": prompt,
                    "duration": min(duration, 60),  # Max 60 seconds
                },
                "parameters": {
                    "aspect_ratio": "9:16",  # TikTok format
                    "style": style,
                    "quality": "high",
                },
            }

            response = await client.post(
                f"{self.base_url}/generate",
                json=payload,
                headers=self._get_headers(),
            )

            if response.status_code != 200:
                logger.error(
                    f"Kling API error: {response.status_code} - {response.text}"
                )
                raise Exception(f"Kling API error: {response.status_code}")

            data = response.json()

            return {
                "job_id": data.get("job_id"),
                "status": data.get("status", "submitted"),
                "webhook_url": data.get("webhook_url"),
            }

        except httpx.RequestError as e:
            logger.error(f"Kling API request error: {e}")
            raise

    async def get_video_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check video generation status

        Returns:
            {"status": "processing|completed|failed", "output_url": str, "error": str}
        """

        if job_id.startswith("mock-"):
            # Simulate completion for mock jobs
            return {
                "status": "completed",
                "output_url": "https://mock-video.s3.amazonaws.com/video.mp4",
            }

        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.base_url}/jobs/{job_id}",
                headers=self._get_headers(),
            )

            if response.status_code != 200:
                logger.error(f"Kling status check error: {response.status_code}")
                raise Exception(f"Kling API error: {response.status_code}")

            data = response.json()

            result = {
                "status": data.get("status"),  # processing, completed, failed
                "output_url": data.get("output", {}).get("video_url"),
            }

            if data.get("status") == "failed":
                result["error"] = data.get("error", "Unknown error")

            return result

        except httpx.RequestError as e:
            logger.error(f"Kling status check error: {e}")
            raise

    async def download_video(self, video_url: str, output_path: str) -> bool:
        """
        Download generated video from Kling to S3

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()

            # Download video
            response = await client.get(video_url, follow_redirects=True)

            if response.status_code != 200:
                logger.error(f"Video download failed: {response.status_code}")
                return False

            # Save to file (in production, would upload to S3)
            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Video downloaded to {output_path}")
            return True

        except httpx.RequestError as e:
            logger.error(f"Video download error: {e}")
            return False


# Singleton instance
_kling_service: Optional[KlingService] = None


def get_kling_service() -> KlingService:
    """Get or create Kling service singleton"""
    global _kling_service
    if _kling_service is None:
        _kling_service = KlingService()
    return _kling_service


async def close_kling_service():
    """Close Kling service on shutdown"""
    global _kling_service
    if _kling_service:
        await _kling_service.close()
