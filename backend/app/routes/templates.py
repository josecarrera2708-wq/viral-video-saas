"""
Templates API routes
GET /api/v1/templates - list available video templates
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.template import VideoTemplate

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

# Predefined templates - these would typically come from DB but we'll seed them
PREDEFINED_TEMPLATES = [
    {
        "id": "template_001",
        "name": "Dynamic Intro",
        "description": "Fast-paced intro with zoom and text effects",
        "category": "business",
        "kling_style_id": "style_dynamic",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Dynamic+Intro"
    },
    {
        "id": "template_002",
        "name": "Smooth Fade",
        "description": "Elegant fade transitions with soft music",
        "category": "business",
        "kling_style_id": "style_smooth",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Smooth+Fade"
    },
    {
        "id": "template_003",
        "name": "Comedy Burst",
        "description": "Energetic transitions for comedy content",
        "category": "humor",
        "kling_style_id": "style_comedy",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Comedy+Burst"
    },
    {
        "id": "template_004",
        "name": "Epic Cinematic",
        "description": "Hollywood-style cinematic effects",
        "category": "business",
        "kling_style_id": "style_cinematic",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Epic+Cinematic"
    },
    {
        "id": "template_005",
        "name": "Minimal Clean",
        "description": "Minimalist design with clean typography",
        "category": "business",
        "kling_style_id": "style_minimal",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Minimal+Clean"
    },
    {
        "id": "template_006",
        "name": "Retro Vibe",
        "description": "80s/90s nostalgic aesthetic",
        "category": "humor",
        "kling_style_id": "style_retro",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Retro+Vibe"
    },
    {
        "id": "template_007",
        "name": "Educational Slide",
        "description": "Perfect for tutorials and educational content",
        "category": "educational",
        "kling_style_id": "style_educational",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Educational"
    },
    {
        "id": "template_008",
        "name": "Glitch Effect",
        "description": "Modern glitch transitions and effects",
        "category": "humor",
        "kling_style_id": "style_glitch",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Glitch+Effect"
    },
    {
        "id": "template_009",
        "name": "Motivational Boost",
        "description": "Inspiring quotes and uplifting music",
        "category": "educational",
        "kling_style_id": "style_motivational",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Motivational"
    },
    {
        "id": "template_010",
        "name": "Dance Sync",
        "description": "Beat-synced transitions for dance content",
        "category": "humor",
        "kling_style_id": "style_dance",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Dance+Sync"
    },
    {
        "id": "template_011",
        "name": "Product Showcase",
        "description": "Highlight product features with spinning effects",
        "category": "business",
        "kling_style_id": "style_showcase",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Showcase"
    },
    {
        "id": "template_012",
        "name": "Travel Vlog",
        "description": "Adventure and travel content template",
        "category": "educational",
        "kling_style_id": "style_travel",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Travel+Vlog"
    },
    {
        "id": "template_013",
        "name": "Neon Lights",
        "description": "Cyberpunk neon aesthetic",
        "category": "humor",
        "kling_style_id": "style_neon",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Neon+Lights"
    },
    {
        "id": "template_014",
        "name": "Typography Focus",
        "description": "Bold text-centric design",
        "category": "business",
        "kling_style_id": "style_typography",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Typography"
    },
    {
        "id": "template_015",
        "name": "3D Rotation",
        "description": "3D spinning and rotation effects",
        "category": "humor",
        "kling_style_id": "style_3d",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=3D+Rotation"
    },
    {
        "id": "template_016",
        "name": "Food & Cooking",
        "description": "Perfect for food and recipe content",
        "category": "educational",
        "kling_style_id": "style_food",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Food"
    },
    {
        "id": "template_017",
        "name": "Vintage Film",
        "description": "Classic film reel aesthetic",
        "category": "business",
        "kling_style_id": "style_vintage",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Vintage+Film"
    },
    {
        "id": "template_018",
        "name": "Makeup/Beauty",
        "description": "Beauty and cosmetics focused template",
        "category": "educational",
        "kling_style_id": "style_beauty",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Beauty"
    },
    {
        "id": "template_019",
        "name": "Sports Highlight",
        "description": "Sports moment highlight reel",
        "category": "humor",
        "kling_style_id": "style_sports",
        "is_trending": False,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Sports"
    },
    {
        "id": "template_020",
        "name": "Futuristic Tech",
        "description": "High-tech sci-fi aesthetic",
        "category": "business",
        "kling_style_id": "style_future",
        "is_trending": True,
        "preview_image_url": "https://via.placeholder.com/300x400?text=Futuristic"
    },
]


@router.get("")
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    trending_only: bool = Query(False, description="Show only trending templates"),
    db: Session = Depends(get_db)
):
    """
    Get list of available video templates

    Query parameters:
    - category: Filter by category (business, humor, educational)
    - trending_only: Show only trending templates

    Returns:
    - List of templates with metadata
    """
    templates = db.query(VideoTemplate).all()

    # If database is empty, seed with predefined templates
    if not templates:
        for template_data in PREDEFINED_TEMPLATES:
            template = VideoTemplate(**template_data)
            db.add(template)
        db.commit()
        templates = db.query(VideoTemplate).all()

    # Apply filters
    if category:
        templates = [t for t in templates if t.category == category]

    if trending_only:
        templates = [t for t in templates if t.is_trending]

    # Sort by trending first, then by usage count
    templates.sort(key=lambda x: (-x.is_trending, -x.usage_count))

    return {
        "templates": [t.to_dict() for t in templates],
        "total": len(templates),
        "categories": ["business", "humor", "educational"]
    }


@router.get("/{template_id}")
async def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get a specific template by ID"""
    template = db.query(VideoTemplate).filter(
        VideoTemplate.id == template_id
    ).first()

    if not template:
        return {"error": "Template not found"}, 404

    return template.to_dict()
