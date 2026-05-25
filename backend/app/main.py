#!/usr/bin/env python3
"""
Viral Video SaaS - FastAPI Backend
Professional platform for generating viral TikTok videos
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import routes
from .routes import auth, videos, payments, templates, user

# Import models to register them with the database
from .models import User, Video, CreditTransaction, VideoTemplate

# Database
from .database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("Starting up Viral Video SaaS API...")
    init_db()
    yield
    print("Shutting down...")

# Initialize FastAPI
app = FastAPI(
    title="Viral Video SaaS API",
    description="Professional video generation platform for TikTok",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local Next.js dev
        "http://localhost:8000",  # Local FastAPI
        "https://viral-video.app",  # Production domain (update as needed)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "viral-video-saas-api"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Viral Video SaaS API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Mount routes
app.include_router(auth.router, tags=["auth"])
app.include_router(videos.router, tags=["videos"])
app.include_router(payments.router, tags=["payments"])
app.include_router(templates.router, tags=["templates"])
app.include_router(user.router, tags=["user"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
