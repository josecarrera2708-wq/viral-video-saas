"""
Video API routes
Create, list, and manage videos
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import logging

from ..database import get_db
from ..models.video import Video
from ..models.user import User
from ..auth import verify_token
from ..services.credit_service import CreditService
from ..services.image_service import ImageService
from ..services.s3_service import get_s3_service
from ..tasks.video_generation import generate_video_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["videos"])


class VideoCreateRequest(BaseModel):
    """Video creation request"""
    title: str
    subtitle: Optional[str] = None
    script: str
    duration: int  # 15, 30, or 60 seconds
    template_id: Optional[str] = None
    language: str = "es"  # es, en


class VideoResponse(BaseModel):
    """Video response"""
    id: str
    title: str
    script: str
    duration: int
    state: str  # pending, processing, completed, failed
    output_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoDetailResponse(VideoResponse):
    """Detailed video response"""
    subtitle: Optional[str] = None
    template_id: Optional[str] = None
    error_message: Optional[str] = None
    kling_job_id: Optional[str] = None


async def get_current_user(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Extract and verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    try:
        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )

        token = parts[1]
        token_data = verify_token(token)

        # Get user
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.post("/videos", response_model=VideoDetailResponse)
async def create_video(
    title: str = Form(...),
    subtitle: Optional[str] = Form(None),
    script: str = Form(...),
    duration: int = Form(...),
    template_id: Optional[str] = Form(None),
    language: str = Form("es"),
    image: UploadFile = File(...),
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create a new video

    Flow:
    1. Validate user has credits
    2. Save image
    3. Enqueue Celery task
    4. Return video record
    """

    # Verify user
    user = await get_current_user(authorization, db)

    # Validate inputs
    if duration not in [15, 30, 60]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be 15, 30, or 60 seconds"
        )

    if len(script) == 0 or len(script) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Script must be 1-500 characters"
        )

    # Calculate credit cost
    credit_cost = CreditService.calculate_video_cost(duration)

    # Check user has enough credits
    if user.credits_balance < credit_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "Insufficient credits",
                "required": credit_cost,
                "available": user.credits_balance,
            }
        )

    # Save and process image
    try:
        # Save temp image
        import tempfile
        import uuid

        temp_dir = tempfile.gettempdir()
        image_id = str(uuid.uuid4())
        image_path = f"{temp_dir}/{image_id}.jpg"

        contents = await image.read()
        with open(image_path, "wb") as f:
            f.write(contents)

        # Validate image
        valid, msg = ImageService.validate_image(image_path)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image: {msg}"
            )

        # Process image
        success, msg, processed_path = ImageService.process_image(image_path)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image processing failed: {msg}"
            )

        # Upload image to S3
        s3 = get_s3_service()
        video_id = str(uuid.uuid4())
        image_url = s3.upload_image(processed_path, user.id, video_id)

        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image processing error: {str(e)}"
        )

    # Create video record
    try:
        video = Video(
            id=video_id,
            user_id=user.id,
            title=title,
            subtitle=subtitle,
            script=script,
            duration=duration,
            template_id=template_id,
            language=language,
            state="pending",
        )
        db.add(video)

        # Debit credits immediately
        user.credits_balance -= credit_cost
        db.commit()
        db.refresh(video)

        logger.info(f"Video created: {video_id}, credits debited: {credit_cost}")

        # Enqueue generation task
        generate_video_task.delay(
            video_id=video_id,
            user_id=user.id,
            image_url=image_url,
            script=script,
            duration=duration,
            template_id=template_id,
        )

        logger.info(f"Video generation task queued: {video_id}")

        return VideoDetailResponse.from_orm(video)

    except Exception as e:
        db.rollback()
        logger.error(f"Video creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video"
        )


@router.get("/videos", response_model=List[VideoResponse])
async def list_videos(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all videos for current user"""

    user = await get_current_user(authorization, db)

    videos = (
        db.query(Video)
        .filter(Video.user_id == user.id)
        .order_by(Video.created_at.desc())
        .all()
    )

    return [VideoResponse.from_orm(v) for v in videos]


@router.get("/videos/{video_id}", response_model=VideoDetailResponse)
async def get_video(
    video_id: str,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get video details"""

    user = await get_current_user(authorization, db)

    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.user_id == user.id)
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return VideoDetailResponse.from_orm(video)


@router.delete("/videos/{video_id}")
async def delete_video(
    video_id: str,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Delete video (refunds credits if <1 hour old)"""

    user = await get_current_user(authorization, db)

    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.user_id == user.id)
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Calculate refund (if <1 hour old)
    from datetime import timedelta
    age = datetime.utcnow() - video.created_at
    if age < timedelta(hours=1) and video.state in ["pending", "processing", "failed"]:
        refund_amount = CreditService.calculate_video_cost(video.duration)
        user.credits_balance += refund_amount
        logger.info(f"Refunded {refund_amount} credits for video {video_id}")

    # Delete from S3
    if video.output_url:
        s3 = get_s3_service()
        s3.delete_file(video.output_url)

    # Delete record
    db.delete(video)
    db.commit()

    return {"status": "deleted"}
