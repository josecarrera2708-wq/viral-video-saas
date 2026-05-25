"""
AWS S3 Service
Upload/download files to/from S3 for videos and images
"""

import boto3
from pathlib import Path
import logging
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3 file operations"""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self.region = settings.aws_region
        self.videos_bucket = settings.s3_bucket_videos
        self.uploads_bucket = settings.s3_bucket_uploads

    def upload_image(
        self,
        file_path: str,
        user_id: str,
        video_id: str,
    ) -> Optional[str]:
        """
        Upload image to S3 temp bucket

        Returns:
            S3 URL if successful, None otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            # Generate S3 key
            key = f"uploads/{user_id}/{video_id}/image.jpg"

            # Upload
            self.s3_client.upload_file(
                str(file_path),
                self.uploads_bucket,
                key,
            )

            # Return public URL
            url = self._get_s3_url(self.uploads_bucket, key)
            logger.info(f"Image uploaded to S3: {url}")
            return url

        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return None

    def upload_video(
        self,
        file_path: str,
        user_id: str,
        video_id: str,
    ) -> Optional[str]:
        """
        Upload generated video to S3

        Returns:
            CloudFront URL if successful, None otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            # Generate S3 key (permanent location)
            key = f"videos/{user_id}/{video_id}/video.mp4"

            # Upload with metadata
            self.s3_client.upload_file(
                str(file_path),
                self.videos_bucket,
                key,
                ExtraArgs={
                    "ContentType": "video/mp4",
                    "Metadata": {
                        "user-id": user_id,
                        "video-id": video_id,
                    },
                },
            )

            # Return CloudFront URL (assuming CloudFront is configured)
            # Format: https://d123.cloudfront.net/videos/{user_id}/{video_id}/video.mp4
            url = f"https://d123.cloudfront.net/{key}"  # Replace d123 with actual distribution
            logger.info(f"Video uploaded to S3: {url}")
            return url

        except Exception as e:
            logger.error(f"S3 video upload error: {e}")
            return None

    def upload_bytes(
        self,
        data: bytes,
        user_id: str,
        file_path: str,
        content_type: str = "application/octet-stream",
    ) -> Optional[str]:
        """
        Upload bytes (e.g., audio) to S3

        Args:
            data: File data as bytes
            user_id: User ID for path
            file_path: Relative file path (e.g., 'audio/video123.mp3')
            content_type: MIME type

        Returns:
            S3 URL if successful, None otherwise
        """
        try:
            key = f"{user_id}/{file_path}"

            self.s3_client.put_object(
                Bucket=self.uploads_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                Metadata={"user-id": user_id},
            )

            url = self._get_s3_url(self.uploads_bucket, key)
            logger.info(f"Bytes uploaded to S3: {url}")
            return url

        except Exception as e:
            logger.error(f"S3 bytes upload error: {e}")
            return None

    def download_file(
        self,
        s3_url: str,
        output_path: str,
    ) -> bool:
        """
        Download file from S3

        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse S3 URL to get bucket and key
            # URL format: https://bucket.s3.region.amazonaws.com/key
            # or: https://d123.cloudfront.net/key

            # For now, use direct S3 download
            if "cloudfront" in s3_url:
                # Extract key from CloudFront URL
                key = s3_url.split("cloudfront.net/", 1)[1]
                bucket = self.videos_bucket
            else:
                # Extract from S3 URL
                parts = s3_url.split("/")
                bucket = parts[2].split(".")[0]
                key = "/".join(parts[3:])

            self.s3_client.download_file(bucket, key, output_path)
            logger.info(f"Downloaded from S3: {output_path}")
            return True

        except Exception as e:
            logger.error(f"S3 download error: {e}")
            return False

    def delete_file(
        self,
        s3_url: str,
    ) -> bool:
        """Delete file from S3"""
        try:
            # Parse URL to get bucket and key
            if "cloudfront" in s3_url:
                key = s3_url.split("cloudfront.net/", 1)[1]
                bucket = self.videos_bucket
            else:
                parts = s3_url.split("/")
                bucket = parts[2].split(".")[0]
                key = "/".join(parts[3:])

            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted from S3: {key}")
            return True

        except Exception as e:
            logger.error(f"S3 delete error: {e}")
            return False

    def _get_s3_url(self, bucket: str, key: str) -> str:
        """Generate S3 URL"""
        return f"https://{bucket}.s3.{self.region}.amazonaws.com/{key}"

    def list_user_videos(self, user_id: str) -> list[dict]:
        """List all videos for a user"""
        try:
            prefix = f"videos/{user_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.videos_bucket,
                Prefix=prefix,
            )

            videos = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    if obj["Key"].endswith(".mp4"):
                        videos.append({
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"],
                        })

            return videos

        except Exception as e:
            logger.error(f"S3 list error: {e}")
            return []


# Singleton instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """Get or create S3 service singleton"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
