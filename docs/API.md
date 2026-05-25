# API Reference - Viral Video SaaS

**Base URL**: `http://localhost:8000` (local) | `https://api.viral-video.app` (production)
**API Version**: v1
**Authentication**: JWT Bearer Token

---

## Authentication Endpoints

### Sign Up
Create a new user account.

**POST** `/auth/signup`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe"
}
```

**Response** (200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe",
    "credits_balance": 0,
    "subscription_tier": "free"
  }
}
```

**Errors**:
- `400` - Email already registered
- `422` - Invalid input

---

### Login
Authenticate and get access token.

**POST** `/auth/login`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response** (200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe",
    "credits_balance": 50,
    "subscription_tier": "free"
  }
}
```

**Errors**:
- `401` - Invalid email or password
- `422` - Invalid input

---

### Get Current User
Get authenticated user profile.

**GET** `/auth/me`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "John Doe",
  "credits_balance": 50,
  "subscription_tier": "free"
}
```

**Errors**:
- `401` - Invalid or missing token
- `404` - User not found

---

### Refresh Token
Get a new access token using refresh token.

**POST** `/auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com"
}
```

---

## Video Endpoints

### Create Video
Generate a new video from image.

**POST** `/api/v1/videos`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Request** (FormData):
```
image: <file>
title: "INCREDIBLE MOMENT"
subtitle: "Watch until end"
script: "Text that will be narrated"
duration: 15
template_id: "realistic"
language: "es"
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "INCREDIBLE MOMENT",
  "script": "Text that will be narrated",
  "duration": 15,
  "state": "pending",
  "output_url": null,
  "created_at": "2026-05-24T12:34:56Z"
}
```

**Errors**:
- `400` - Invalid image or input
- `401` - Not authenticated
- `402` - Insufficient credits (see response.detail for required vs available)
- `422` - Invalid input parameters

---

### List Videos
Get all videos for authenticated user.

**GET** `/api/v1/videos`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "INCREDIBLE MOMENT",
    "script": "Text that will be narrated",
    "duration": 15,
    "state": "completed",
    "output_url": "https://d123.cloudfront.net/videos/user/video.mp4",
    "created_at": "2026-05-24T12:34:56Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "ANOTHER VIDEO",
    "script": "Different narration",
    "duration": 30,
    "state": "processing",
    "output_url": null,
    "created_at": "2026-05-24T11:34:56Z"
  }
]
```

**Errors**:
- `401` - Not authenticated

---

### Get Video Details
Get specific video status and details.

**GET** `/api/v1/videos/{video_id}`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "INCREDIBLE MOMENT",
  "subtitle": "Watch until end",
  "script": "Text that will be narrated",
  "duration": 15,
  "template_id": "realistic",
  "state": "processing",
  "output_url": null,
  "created_at": "2026-05-24T12:34:56Z",
  "kling_job_id": "job_12345",
  "error_message": null
}
```

**States**:
- `pending` - Queued for generation
- `processing` - Kling is generating video
- `completed` - Ready for download
- `failed` - Generation failed (see error_message)

**Errors**:
- `401` - Not authenticated
- `404` - Video not found or not owned by user

---

### Delete Video
Delete video and optionally refund credits.

**DELETE** `/api/v1/videos/{video_id}`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "status": "deleted"
}
```

**Refund Rules**:
- Video deleted <1 hour after creation AND state is pending/processing/failed → Full refund
- Video completed OR >1 hour old → No refund

**Errors**:
- `401` - Not authenticated
- `404` - Video not found

---

## Example Usage

### Using cURL

```bash
# Sign up
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "name": "Test User"
  }'

# Save token from response
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Get current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Create video
curl -X POST http://localhost:8000/api/v1/videos \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@image.jpg" \
  -F "title=TEST" \
  -F "script=This is a test" \
  -F "duration=15" \
  -F "template_id=realistic" \
  -F "language=es"

# List videos
curl -X GET http://localhost:8000/api/v1/videos \
  -H "Authorization: Bearer $TOKEN"

# Get video status
curl -X GET http://localhost:8000/api/v1/videos/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"

# Delete video
curl -X DELETE http://localhost:8000/api/v1/videos/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Sign up
response = requests.post(f"{BASE_URL}/auth/signup", json={
    "email": "test@example.com",
    "password": "test123",
    "name": "Test User"
})
data = response.json()
token = data["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Create video
with open("image.jpg", "rb") as f:
    files = {"image": f}
    data = {
        "title": "TEST",
        "script": "This is a test",
        "duration": 15,
        "template_id": "realistic",
        "language": "es"
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/videos",
        headers=headers,
        files=files,
        data=data
    )
    video = response.json()
    print(f"Video created: {video['id']}")

# Poll for status
import time
video_id = video["id"]
while True:
    response = requests.get(
        f"{BASE_URL}/api/v1/videos/{video_id}",
        headers=headers
    )
    video = response.json()
    print(f"Status: {video['state']}")
    
    if video["state"] == "completed":
        print(f"Download: {video['output_url']}")
        break
    
    time.sleep(2)
```

---

## Credit System

### Pricing

- **Free Tier**: 5 videos/month, watermarked
- **Creator**: $9.99/month = 50 credits
- **Pro**: $19.99/month = 125 credits  
- **Business**: $49.99/month = 400 credits

### Cost Calculation

```
Video Cost = 30 + (duration_seconds × 0.07)

Examples:
- 15 second video  = 30 + (15 × 0.07) = 31.05 credits
- 30 second video  = 30 + (30 × 0.07) = 32.10 credits
- 60 second video  = 30 + (60 × 0.07) = 34.20 credits
```

### Refund Policy

- Videos deleted <1 hour after creation: Full refund
- Videos older than 1 hour: No refund
- Failed videos: Automatic refund

---

## User Endpoints

### Get User Profile
Get current authenticated user's profile and credits.

**GET** `/api/v1/user`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "John Doe",
  "subscription_tier": "free",
  "credits_balance": 100,
  "videos_created": 5,
  "created_at": "2026-05-24T10:00:00Z",
  "stripe_customer_id": "cus_xyz123"
}
```

**Errors**:
- `401` - Not authenticated
- `404` - User not found

---

### Update User Profile
Update user name or email.

**PATCH** `/api/v1/user`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
  "name": "New Name",
  "email": "newemail@example.com"
}
```

**Response** (200):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "newemail@example.com",
  "name": "New Name",
  "subscription_tier": "free",
  "credits_balance": 100,
  "message": "Profile updated successfully"
}
```

**Errors**:
- `401` - Not authenticated
- `409` - Email already in use

---

### Get Transaction History
Get credit transaction history.

**GET** `/api/v1/user/transactions?limit=50&offset=0`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "transactions": [
    {
      "id": "txn_001",
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "amount": -32,
      "type": "debit",
      "reason": "Video generation - 30 seconds",
      "created_at": "2026-05-24T12:34:56Z"
    },
    {
      "id": "txn_002",
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "amount": 100,
      "type": "credit",
      "reason": "Purchase - Basic Package",
      "created_at": "2026-05-24T11:00:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

---

### Get User Statistics
Get detailed user stats.

**GET** `/api/v1/user/stats`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "total_videos": 15,
  "videos_this_month": 8,
  "videos_by_status": {
    "completed": 12,
    "processing": 2,
    "failed": 1
  },
  "credits_spent_this_month": 250,
  "current_credits": 100,
  "subscription_tier": "free"
}
```

---

## Templates Endpoints

### List All Templates
Get available video templates.

**GET** `/api/v1/templates?category=business&trending_only=false`

**Query Parameters**:
- `category` (optional): Filter by category (business, humor, educational)
- `trending_only` (optional): Show only trending templates (true/false)

**Response** (200):
```json
{
  "templates": [
    {
      "id": "template_001",
      "name": "Dynamic Intro",
      "description": "Fast-paced intro with zoom and text effects",
      "category": "business",
      "preview_image_url": "https://...",
      "kling_style_id": "style_dynamic",
      "duration_seconds": 30,
      "is_trending": true,
      "usage_count": 1520
    },
    {
      "id": "template_002",
      "name": "Comedy Burst",
      "description": "Energetic transitions for comedy content",
      "category": "humor",
      "preview_image_url": "https://...",
      "kling_style_id": "style_comedy",
      "duration_seconds": 30,
      "is_trending": true,
      "usage_count": 890
    }
  ],
  "total": 20,
  "categories": ["business", "humor", "educational"]
}
```

---

### Get Single Template
Get details of a specific template.

**GET** `/api/v1/templates/{template_id}`

**Response** (200):
```json
{
  "id": "template_001",
  "name": "Dynamic Intro",
  "description": "Fast-paced intro with zoom and text effects",
  "category": "business",
  "preview_image_url": "https://...",
  "kling_style_id": "style_dynamic",
  "duration_seconds": 30,
  "is_trending": true,
  "usage_count": 1520
}
```

**Errors**:
- `404` - Template not found

---

## Payment Endpoints

### Get Credit Packages
List available credit packages for purchase.

**GET** `/api/v1/payments/packages`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "packages": [
    {
      "id": "basic",
      "name": "Basic Package",
      "credits": 50,
      "price_usd": 9.99,
      "price_per_credit": 0.20,
      "description": "Perfect for getting started"
    },
    {
      "id": "pro",
      "name": "Pro Package",
      "credits": 125,
      "price_usd": 19.99,
      "price_per_credit": 0.16,
      "description": "Best value for creators"
    },
    {
      "id": "business",
      "name": "Business Package",
      "credits": 400,
      "price_usd": 49.99,
      "price_per_credit": 0.125,
      "description": "For serious creators"
    }
  ]
}
```

---

### Create Checkout Session
Create a Stripe checkout session for credit purchase.

**POST** `/api/v1/payments/checkout`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request**:
```json
{
  "package_id": "pro"
}
```

**Response** (200):
```json
{
  "session_id": "cs_test_123",
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_123",
  "package_id": "pro",
  "amount_usd": 19.99,
  "credits": 125
}
```

**Errors**:
- `401` - Not authenticated
- `404` - Package not found

---

### Get Payment Transaction History
Get user's payment transaction history.

**GET** `/api/v1/payments/transactions?limit=50&offset=0`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "transactions": [
    {
      "id": "pay_001",
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "provider": "stripe",
      "amount": 19.99,
      "currency": "USD",
      "status": "completed",
      "created_at": "2026-05-24T10:00:00Z"
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 402 | Payment Required - Insufficient credits |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid parameters |
| 500 | Server Error - Unexpected error |

---

## Rate Limiting

**Coming in SPRINT 3**
- 100 requests/minute per user
- 10 concurrent video generations per user

---

## Pagination

**Coming in SPRINT 3**
- `GET /api/v1/videos?skip=0&limit=20`

---

## Webhooks

**Coming in SPRINT 3**
- Kling completion notifications
- Stripe payment webhooks
- User notifications via email

---

## SDKs

**Official SDKs Coming Soon**
- Python SDK
- JavaScript/TypeScript SDK
- Go SDK

---

**Last Updated**: May 24, 2026
**API Version**: 1.0
**Status**: SPRINT 3 Complete - All core endpoints ready for testing
