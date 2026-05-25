"""
Video generation tasks
Async Celery tasks for creating videos
"""

import asyncio
import logging
from celery import Task
from pathlib import Path
from .celery_app import celery_app
from ..database import SessionLocal
from ..models.video import Video
from ..services.kling_service import get_kling_service
from ..services.s3_service import get_s3_service
from ..services.audio_service import AudioService
from ..services.credit_service import CreditService
from ..config import settings

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Task with error callback"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Update video status in DB
        video_id = kwargs.get("video_id")
        if video_id:
            db = SessionLocal()
            try:
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.state = "failed"
                    video.error_message = str(exc)
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to update video status: {e}")
            finally:
                db.close()


@celery_app.task(base=CallbackTask, bind=True)
def generate_video_task(
    self,
    video_id: str,
    user_id: str,
    image_url: str,
    script: str,
    duration: int,
    template_id: str = None,
):
    """
    Main video generation task

    Flow:
    1. Get Kling to generate video
    2. Poll for completion
    3. Download to S3
    4. Update DB with result
    """
    logger.info(f"Starting video generation: {video_id}")

    db = SessionLocal()
    kling = get_kling_service()
    s3 = get_s3_service()
    audio = AudioService()

    try:
        # Update video status
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise Exception(f"Video {video_id} not found")

        video.state = "processing"
        db.commit()

        # Generate audio narration (optional - for future use/analytics)
        # Currently, Kling handles audio generation integrated with video
        if script and False:  # Disabled for now - Kling generates audio
            logger.info(f"Generating audio narration...")
            self.update_state(state="PROGRESS", meta={"status": "generating_audio"})
            try:
                audio_bytes = asyncio.run(audio.generate_audio(script))
                if audio_bytes:
                    audio_url = s3.upload_bytes(
                        audio_bytes,
                        user_id,
                        f"audio/{video_id}.mp3",
                        content_type="audio/mpeg"
                    )
                    logger.info(f"Audio uploaded: {audio_url}")
            except Exception as e:
                logger.warning(f"Audio generation failed (non-critical): {e}")

        # Request video generation from Kling
        logger.info(f"Requesting Kling video generation...")
        self.update_state(state="PROGRESS", meta={"status": "requesting_kling"})

        result = asyncio.run(
            kling.generate_video(
                image_url=image_url,
                prompt=script,
                duration=duration,
                style=template_id or "realistic",
            )
        )

        job_id = result.get("job_id")
        video.kling_job_id = job_id
        db.commit()

        logger.info(f"Kling job created: {job_id}")

        # Poll for completion (max 5 minutes)
        max_polls = 60
        poll_interval = 5  # seconds

        for poll_count in range(max_polls):
            logger.info(f"Polling Kling status (attempt {poll_count + 1}/{max_polls})")
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": "generating_video",
                    "progress": int((poll_count / max_polls) * 100),
                },
            )

            # Check status
            status_result = asyncio.run(kling.get_video_status(job_id))
            status = status_result.get("status")

            if status == "completed":
                video_url = status_result.get("output_url")
                logger.info(f"Video generated: {video_url}")

                # Download to S3
                logger.info(f"Downloading video from Kling...")
                self.update_state(state="PROGRESS", meta={"status": "downloading"})

                temp_path = f"/tmp/{video_id}.mp4"
                success = asyncio.run(kling.download_video(video_url, temp_path))

                if success:
                    # Upload to S3
                    logger.info(f"Uploading to S3...")
                    self.update_state(state="PROGRESS", meta={"status": "uploading"})

                    s3_url = s3.upload_video(temp_path, user_id, video_id)

                    if s3_url:
                        # Update video record
                        video.state = "completed"
                        video.output_url = s3_url
                        db.commit()

                        # Cleanup temp file
                        Path(temp_path).unlink(missing_ok=True)

                        logger.info(f"Video generation complete: {video_id}")
                        self.update_state(state="SUCCESS", meta={"status": "completed"})
                        return {"status": "success", "video_id": video_id}
                    else:
                        raise Exception("Failed to upload video to S3")
                else:
                    raise Exception("Failed to download video from Kling")

            elif status == "failed":
                error = status_result.get("error", "Unknown error")
                raise Exception(f"Kling video generation failed: {error}")

            # Wait before next poll
            import time
            time.sleep(poll_interval)

        # Timeout
        raise Exception("Video generation timeout (exceeded 5 minutes)")

    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        # Status will be updated in on_failure callback
        raise

    finally:
        db.close()


@celery_app.task
def cleanup_expired_videos():
    """
    Cleanup videos older than 7 days
    Run periodically (daily)
    """
    logger.info("Cleaning up expired videos...")
    from datetime import datetime, timedelta

    db = SessionLocal()
    s3 = get_s3_service()

    try:
        # Find old videos
        expiration_date = datetime.utcnow() - timedelta(days=7)
        old_videos = db.query(Video).filter(
            Video.created_at < expiration_date,
            Video.state == "completed",
        ).all()

        for video in old_videos:
            try:
                if video.output_url:
                    s3.delete_file(video.output_url)
                video.state = "deleted"
                db.commit()
                logger.info(f"Deleted old video: {video.id}")
            except Exception as e:
                logger.error(f"Failed to delete video {video.id}: {e}")

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")

    finally:
        db.close()
