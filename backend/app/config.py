"""
Configuration for Viral Video SaaS backend
Loads from environment variables
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/viral_db"

    # JWT / Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None

    # Kling API
    kling_api_key: Optional[str] = None
    kling_api_base_url: str = "https://api.kling.com/v1"

    # D-ID API (backup)
    did_api_key: Optional[str] = None
    did_api_base_url: str = "https://api.d-id.com"

    # AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_videos: str = "viral-videos-prod"
    s3_bucket_uploads: str = "viral-uploads-temp"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # App settings
    app_name: str = "Viral Video SaaS"
    debug: bool = True
    max_upload_size_mb: int = 50
    video_credit_cost_per_sec: float = 0.07
    video_credit_overhead: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
