# Quick Start - Viral Video SaaS

Get the platform running in 5 minutes.

## Prerequisites

- Docker Desktop installed and running
- Node.js 18+ installed
- Python 3.11+ installed
- Git installed

## Step 1: Start Backend Services (1 min)

```bash
cd C:\Users\mario\viral-video-saas

# Start Docker containers (PostgreSQL, Redis, FastAPI)
docker-compose up -d

# Wait for services to start (~30 seconds)
sleep 30

# Verify services are running
docker-compose ps
# Should show: postgres (healthy), redis (healthy), backend (healthy)
```

## Step 2: Setup Backend (1 min)

```bash
cd backend

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run tests to verify setup
pytest tests/ -v --tb=short
# Should show: 33+ tests passing
```

## Step 3: Start Frontend (2 min)

```bash
cd ../frontend

# Install dependencies
npm install

# Start dev server (runs in background)
npm run dev &
```

## Step 4: Verify Everything (1 min)

Open your browser and visit:

### Frontend
- **URL**: http://localhost:3000
- **Expected**: Landing page with pricing table, "Sign Up" button
- **Action**: Click "Sign Up"

### Backend API
- **URL**: http://localhost:8000/docs
- **Expected**: Swagger UI with all API endpoints
- **Check**: 30+ endpoints listed

### Database
```bash
# Verify database is ready
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"viral-video-saas-api"}
```

---

## Complete Workflow Test (5 min)

### 1. Create Account
```bash
# Visit http://localhost:3000/auth/signup
# Fill: Email, Password, Name
# Click: Sign Up
```

### 2. View Templates
```bash
# You'll be redirected to dashboard
# Click: "Create Video"
# You should see: 20+ templates in different styles
```

### 3. Generate a Video
```bash
# 1. Click any template
# 2. Upload an image (JPG/PNG)
# 3. Enter: Title, Description, Script
# 4. Select duration: 15s, 30s, or 60s
# 5. Click: "Generate Video"
# Expected: "Generating..." status appears
```

### 4. Check Credits
```bash
# Click: Account (top right)
# You should see:
#   - Current credit balance
#   - Video cost: 30 + (duration × 0.07)
#   - Transaction history
```

### 5. Buy Credits (Test)
```bash
# Click: "Billing"
# Select: "Basic" package ($9.99 → 50 credits)
# Click: "Checkout"
# Use Stripe test card: 4242 4242 4242 4242
# Any future date, any CVV
# Credits should update after payment
```

---

## Common Commands

### Docker
```bash
# View logs
docker-compose logs backend -f

# Stop services
docker-compose down

# Restart everything
docker-compose restart
```

### Backend
```bash
# Run tests
cd backend
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html
# Open: htmlcov/index.html in browser

# Access database
docker-compose exec postgres psql -U postgres -d viral_db
# In psql:
# \dt           - List tables
# SELECT * FROM users;  - See users
# \q            - Exit
```

### Frontend
```bash
cd frontend

# Development server (auto-reload)
npm run dev

# Production build
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
```

---

## API Endpoints (Quick Reference)

### Authentication
```bash
# Sign Up
POST /auth/signup
{"email":"user@example.com","password":"pass123","name":"John"}

# Login
POST /auth/login
{"email":"user@example.com","password":"pass123"}
```

### Videos
```bash
# Create video (requires auth)
POST /api/v1/videos
Form: image, title, script, duration, template_id

# List videos
GET /api/v1/videos

# Get video status
GET /api/v1/videos/{video_id}

# Delete video
DELETE /api/v1/videos/{video_id}
```

### User
```bash
# Get profile
GET /api/v1/user

# Get stats
GET /api/v1/user/stats

# Get transaction history
GET /api/v1/user/transactions
```

### Templates
```bash
# List templates
GET /api/v1/templates?category=business&trending_only=false

# Get single template
GET /api/v1/templates/{template_id}
```

### Payments
```bash
# Get packages
GET /api/v1/payments/packages

# Create checkout
POST /api/v1/payments/checkout
{"package_id":"pro"}
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F

# Or use different port:
docker-compose -f docker-compose.yml -e BACKEND_PORT=8001 up -d
```

### Database Connection Error
```bash
# Ensure PostgreSQL is running
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose up -d
```

### Frontend Can't Connect to Backend
```bash
# 1. Check backend is healthy
curl http://localhost:8000/health

# 2. Check CORS settings in backend/app/main.py
# Should have: "http://localhost:3000" in allow_origins

# 3. Clear browser cache
# Ctrl+Shift+Delete (Chrome/Edge)
```

### Tests Failing
```bash
# Clean up any old test artifacts
cd backend
rm -rf .pytest_cache __pycache__
rm -f test.db

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Run tests again
pytest tests/ -v
```

---

## Next Steps

### After Local Testing:
1. ✅ Run all tests: `pytest backend/tests/ -v`
2. ✅ Test end-to-end: Create → Pay → Download flow
3. ✅ Check coverage: `pytest backend/tests/ --cov=app`
4. 📋 See [PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) for launch prep
5. 🚀 See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for AWS deployment

### Customization:
- Edit templates in `backend/app/routes/templates.py`
- Update pricing in `backend/app/services/stripe_service.py`
- Customize frontend theme in `frontend/tailwind.config.js`
- Add more API endpoints following existing patterns

### API Keys Required for Full Functionality:
- [ ] Stripe API Key (test or live)
- [ ] Kling API Key (for video generation)
- [ ] AWS Credentials (for S3 storage)
- [ ] ElevenLabs API Key (optional, for premium audio)

---

## Monitoring

### Health Checks
```bash
# Backend API health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Database
docker-compose exec postgres psql -U postgres -d viral_db -c "SELECT 1;"

# Redis
docker-compose exec redis redis-cli ping
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs backend -f
docker-compose logs postgres -f
docker-compose logs redis -f
```

---

## Architecture Overview

```
┌─────────────────┐
│  Browser        │
│ localhost:3000  │
└────────┬────────┘
         │ REST API
         ↓
┌─────────────────┐     ┌──────────────┐
│  Next.js 15     │────→│   FastAPI    │
│  Frontend       │     │ localhost    │
└─────────────────┘     │   :8000      │
                        └────┬─────────┘
                             │
                   ┌─────────┼─────────┐
                   ↓         ↓         ↓
            ┌──────────┐ ┌────────┐ ┌──────────┐
            │PostgreSQL│ │ Redis  │ │Kling API │
            │ Database │ │ Cache  │ │(Video)   │
            └──────────┘ └────────┘ └──────────┘
                              │
                              ↓
                        ┌──────────────┐
                        │ AWS S3       │
                        │ + CloudFront │
                        │ (Video CDN)  │
                        └──────────────┘
```

---

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Setup Guide**: [docs/SETUP.md](docs/SETUP.md)
- **API Reference**: [docs/API.md](docs/API.md)
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Production Checklist**: [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md)
- **SPRINT 3 Summary**: [docs/SPRINT3_SUMMARY.md](docs/SPRINT3_SUMMARY.md)

---

**Status**: ✅ Ready for Local Development & Testing
**Last Updated**: May 24, 2026
**Estimated Setup Time**: 5 minutes
