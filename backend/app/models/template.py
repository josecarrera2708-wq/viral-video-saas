"""
Video template model - Predefined video styles/effects
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime
from ..database import Base


class VideoTemplate(Base):
    """Video template with effects and styling options"""
    __tablename__ = "video_templates"

    id = Column(String, primary_key=True)  # e.g., "style_001"
    name = Column(String, nullable=False)  # e.g., "Dynamic Intro"
    description = Column(String)
    category = Column(String)  # e.g., "business", "humor", "educational"
    preview_image_url = Column(String)  # URL to preview thumbnail
    kling_style_id = Column(String)  # Kling API style identifier
    duration_seconds = Column(Integer, default=30)  # Default duration
    is_trending = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "preview_image_url": self.preview_image_url,
            "kling_style_id": self.kling_style_id,
            "duration_seconds": self.duration_seconds,
            "is_trending": self.is_trending,
            "usage_count": self.usage_count,
        }
