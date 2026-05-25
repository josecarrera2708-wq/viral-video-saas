"""
Video endpoint tests
Tests for complete video creation pipeline
"""

import pytest
import io
from unittest.mock import patch, MagicMock


def test_list_user_videos(client, token, db, db_user):
    """Test listing user's videos"""
    from ..models.video import Video

    # Create test videos
    for i in range(3):
        video = Video(
            user_id=db_user.id,
            title=f"Test Video {i}",
            script="Test script",
            state="completed",
            duration=30,
            output_url=f"https://videos.s3.amazonaws.com/video{i}.mp4"
        )
        db.add(video)
    db.commit()

    response = client.get(
        "/api/v1/videos",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "videos" in data
    assert len(data["videos"]) == 3


def test_create_video_success(client, token, db, db_user):
    """Test creating a video with all required fields"""
    # Mock the image upload and Celery task
    with patch("celery.Task.apply_async") as mock_task:
        mock_task.return_value = MagicMock(id="task_123")

        # Create test image
        image_data = b"fake image data"
        image_file = ("test.jpg", io.BytesIO(image_data), "image/jpeg")

        response = client.post(
            "/api/v1/videos",
            data={
                "title": "Test Video",
                "subtitle": "Subtitle",
                "script": "This is a test script",
                "duration": 30,
                "template_id": "template_001",
                "language": "en"
            },
            files={"image": image_file},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
        assert "state" in data
        assert data["state"] == "pending"


def test_create_video_insufficient_credits(client, token, db, db_user):
    """Test creating video with insufficient credits"""
    # Set user credits to 0
    db_user.credits_balance = 0
    db.commit()

    image_data = b"fake image data"
    image_file = ("test.jpg", io.BytesIO(image_data), "image/jpeg")

    response = client.post(
        "/api/v1/videos",
        data={
            "title": "Test Video",
            "script": "Test script",
            "duration": 30,
            "template_id": "template_001"
        },
        files={"image": image_file},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 402  # Payment Required


def test_get_video_details(client, token, db, db_user):
    """Test getting details of a specific video"""
    from ..models.video import Video

    video = Video(
        user_id=db_user.id,
        title="Test Video",
        script="Test script",
        state="completed",
        duration=30,
        output_url="https://videos.s3.amazonaws.com/test.mp4"
    )
    db.add(video)
    db.commit()

    response = client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == video.id
    assert data["title"] == "Test Video"
    assert data["state"] == "completed"
    assert data["output_url"] == "https://videos.s3.amazonaws.com/test.mp4"


def test_delete_video(client, token, db, db_user):
    """Test deleting a video"""
    from ..models.video import Video

    video = Video(
        user_id=db_user.id,
        title="Test Video",
        script="Test script",
        state="completed",
        duration=30,
        output_url="https://videos.s3.amazonaws.com/test.mp4"
    )
    db.add(video)
    db.commit()

    response = client.delete(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Verify video is deleted
    deleted_video = db.query(Video).filter(Video.id == video.id).first()
    assert deleted_video is None or deleted_video.state == "deleted"


def test_create_video_invalid_image(client, token):
    """Test creating video with invalid image"""
    # Try to create without image
    response = client.post(
        "/api/v1/videos",
        data={
            "title": "Test Video",
            "script": "Test script",
            "duration": 30
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


def test_create_video_invalid_duration(client, token):
    """Test creating video with invalid duration"""
    image_data = b"fake image data"
    image_file = ("test.jpg", io.BytesIO(image_data), "image/jpeg")

    response = client.post(
        "/api/v1/videos",
        data={
            "title": "Test Video",
            "script": "Test script",
            "duration": 1000,  # Too long
            "template_id": "template_001"
        },
        files={"image": image_file},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


def test_get_video_no_permission(client, db, db_user):
    """Test getting video of another user"""
    from ..models.user import User
    from ..models.video import Video
    from ..auth import get_password_hash

    # Create another user
    other_user = User(
        email="other@example.com",
        name="Other User",
        hashed_password=get_password_hash("pass123"),
        subscription_tier="free",
        credits_balance=0
    )
    db.add(other_user)
    db.commit()

    # Create video for other user
    video = Video(
        user_id=other_user.id,
        title="Other Video",
        script="Test script",
        state="completed",
        duration=30,
        output_url="https://videos.s3.amazonaws.com/test.mp4"
    )
    db.add(video)
    db.commit()

    # Try to get video as different user
    from ..auth import create_access_token
    token = create_access_token(db_user.id, db_user.email)

    response = client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_video_processing_status(client, token, db, db_user):
    """Test checking video generation status"""
    from ..models.video import Video

    video = Video(
        user_id=db_user.id,
        title="Processing Video",
        script="Test script",
        state="processing",
        duration=30
    )
    db.add(video)
    db.commit()

    response = client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "processing"
    assert "progress" in data or "status" in data
