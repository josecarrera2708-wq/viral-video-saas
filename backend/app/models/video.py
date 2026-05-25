"""
Video model
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
from uuid import uuid4
from ..database import Base


class Video(Base):
    """Generated video model"""
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Content
    title = Column(String(50), nullable=True)
    subtitle = Column(String(50), nullable=True)
    script = Column(Text, nullable=True)
    template_id = Column(String, nullable=True)

    # Video settings
    duration = Column(Integer, default=15)  # seconds
    language = Column(String, default="es")

    # Status tracking
    state = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Output
    output_url = Column(String, nullable=True)  # CloudFront URL
    file_size_mb = Column(Integer, nullable=True)
    kling_job_id = Column(String, nullable=True)  # Kling API job tracking

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, nullable=True)  # S3 auto-delete after 7 days

    def __repr__(self):
        return f"<Video {self.id} - {self.state}>"
