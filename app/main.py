from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import uuid
import json

app = FastAPI(
    title="Viral Video SaaS API",
    version="1.0.0",
    description="Professional AI Video Generation Platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELS =====
class User(BaseModel):
    id: str
    email: str
    name: str
    credits_balance: int = 100
    subscription_tier: str = "free"

class Video(BaseModel):
    id: str
    title: str
    state: str
    duration: int
    created_at: str
    output_url: str = None
    progress: int = 0

class PaymentPackage(BaseModel):
    id: str
    name: str
    credits: int
    price_usd: float
    price_per_credit: float

# ===== DEMO DATA =====
DEMO_USERS = {}
DEMO_VIDEOS = {}
DEMO_PACKAGES = [
    {"id": "basic", "name": "Basic", "credits": 50, "price_usd": 9.99, "price_per_credit": 0.20},
    {"id": "pro", "name": "Pro", "credits": 125, "price_usd": 19.99, "price_per_credit": 0.16},
    {"id": "business", "name": "Business", "credits": 400, "price_usd": 49.99, "price_per_credit": 0.12},
]

# ===== HEALTH & STATUS =====
@app.get("/")
async def read_root():
    return {
        "status": "healthy",
        "app": "Viral Video SaaS Backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "auth": "/auth/...",
            "videos": "/api/v1/videos",
            "payments": "/api/v1/payments/...",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    }

# ===== AUTHENTICATION =====
@app.post("/auth/signup")
async def signup(email: str, password: str, name: str):
    if email in DEMO_USERS:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": email,
        "name": name,
        "password_hash": hash(password),
        "credits_balance": 100,
        "subscription_tier": "free",
        "created_at": datetime.now().isoformat()
    }
    DEMO_USERS[email] = user

    return {
        "access_token": f"token_{user_id}",
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
            "name": name,
            "credits_balance": 100
        }
    }

@app.post("/auth/login")
async def login(email: str, password: str):
    if email not in DEMO_USERS:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = DEMO_USERS[email]
    return {
        "access_token": f"token_{user['id']}",
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "credits_balance": user['credits_balance']
        }
    }

@app.get("/auth/me")
async def get_me(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Find user by token
    for email, user in DEMO_USERS.items():
        if authorization.endswith(user['id']):
            return {
                "id": user['id'],
                "email": user['email'],
                "name": user['name'],
                "credits_balance": user['credits_balance'],
                "subscription_tier": user['subscription_tier']
            }

    raise HTTPException(status_code=401, detail="Invalid token")

# ===== VIDEO CREATION =====
@app.post("/api/v1/videos")
async def create_video(
    authorization: str = None,
    title: str = Form(...),
    subtitle: str = Form(...),
    script: str = Form(...),
    duration: int = Form(...),
    template_id: str = Form(...),
    language: str = Form(...),
    image: UploadFile = File(...)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get user
    user = None
    for email, u in DEMO_USERS.items():
        if authorization.endswith(u['id']):
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Calculate credits needed
    credits_needed = 30 + int(duration * 0.07)

    if user['credits_balance'] < credits_needed:
        raise HTTPException(
            status_code=402,
            detail={
                "required": credits_needed,
                "available": user['credits_balance']
            }
        )

    # Deduct credits
    user['credits_balance'] -= credits_needed

    # Create video record
    video_id = str(uuid.uuid4())
    video = {
        "id": video_id,
        "user_email": user['email'],
        "title": title,
        "subtitle": subtitle,
        "script": script,
        "duration": duration,
        "template_id": template_id,
        "language": language,
        "state": "processing",  # Start in processing (skips queue)
        "progress": 50,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
        "output_url": None
    }
    DEMO_VIDEOS[video_id] = video

    return {
        "id": video_id,
        "state": "processing",
        "created_at": video['created_at']
    }

@app.get("/api/v1/videos")
async def list_videos(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = None
    for email, u in DEMO_USERS.items():
        if authorization.endswith(u['id']):
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_videos = [v for v in DEMO_VIDEOS.values() if v['user_email'] == user['email']]
    return user_videos

@app.get("/api/v1/videos/{video_id}")
async def get_video(video_id: str, authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if video_id not in DEMO_VIDEOS:
        raise HTTPException(status_code=404, detail="Video not found")

    video = DEMO_VIDEOS[video_id]

    # Simulate video generation progress
    if video['state'] == 'processing':
        import random
        if random.random() > 0.7:  # 30% chance to complete
            video['state'] = 'completed'
            video['progress'] = 100
            video['output_url'] = f"https://viral-processed-8902.s3.amazonaws.com/videos/{video_id}.mp4"
        else:
            video['progress'] = min(99, video['progress'] + random.randint(5, 15))

    return {
        "id": video['id'],
        "title": video['title'],
        "state": video['state'],
        "duration": video['duration'],
        "created_at": video['created_at'],
        "output_url": video['output_url'],
        "progress": video['progress']
    }

@app.delete("/api/v1/videos/{video_id}")
async def delete_video(video_id: str, authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if video_id in DEMO_VIDEOS:
        del DEMO_VIDEOS[video_id]

    return {"status": "deleted"}

# ===== PAYMENTS =====
@app.get("/api/v1/payments/packages")
async def get_packages():
    return {
        "packages": DEMO_PACKAGES
    }

@app.post("/api/v1/payments/checkout")
async def checkout(package_id: str = Form(...), authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = None
    for email, u in DEMO_USERS.items():
        if authorization.endswith(u['id']):
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    package = next((p for p in DEMO_PACKAGES if p['id'] == package_id), None)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # Simulate Stripe checkout (in demo, auto-succeed)
    session_id = f"cs_{uuid.uuid4().hex[:24]}"

    # Auto-approve in demo (for testing)
    user['credits_balance'] += package['credits']

    return {
        "url": f"https://checkout.stripe.com/pay/{session_id}",
        "session_id": session_id,
        "credits_added": package['credits']
    }

@app.get("/api/v1/payments/transactions")
async def get_transactions(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Return demo transactions
    return {
        "transactions": [
            {
                "id": str(uuid.uuid4()),
                "amount": 50,
                "type": "credit",
                "reason": "signup_bonus",
                "created_at": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]
    }

# ===== WEBHOOKS =====
@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    # In demo, just acknowledge
    return {"status": "received"}

@app.post("/webhooks/kling")
async def kling_webhook(request: Request):
    # In demo, just acknowledge
    return {"status": "received"}

# ===== TEMPLATES =====
@app.get("/api/v1/templates")
async def get_templates():
    return {
        "templates": [
            {"id": "realistic", "name": "Realistic", "icon": "🎬"},
            {"id": "cinematic", "name": "Cinematic", "icon": "🎥"},
            {"id": "anime", "name": "Anime", "icon": "✨"},
            {"id": "artistic", "name": "Artistic", "icon": "🎨"},
            {"id": "horror", "name": "Horror", "icon": "👻"},
            {"id": "comedy", "name": "Comedy", "icon": "😂"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
