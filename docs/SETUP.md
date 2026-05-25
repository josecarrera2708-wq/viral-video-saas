# Local Development Setup

Complete guide to set up the Viral Video SaaS project locally.

## Prerequisites

- **Windows 11** (or macOS/Linux)
- **Docker Desktop** - https://www.docker.com/products/docker-desktop
- **Node.js 18+** - https://nodejs.org/
- **Python 3.11+** - https://www.python.org/
- **Git** - https://git-scm.com/

## Step 1: Clone and Initial Setup

```bash
# Navigate to your projects directory
cd C:\Users\mario\

# Repository is at C:\Users\mario\viral-video-saas
cd viral-video-saas

# Copy environment files
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env.local
```

## Step 2: Start Docker Services

```bash
# Start PostgreSQL, Redis, and FastAPI backend
docker-compose up -d

# Check status
docker-compose ps

# Verify services are healthy
docker-compose logs postgres  # Should show "database system is ready"
docker-compose logs redis     # Should show "Ready to accept connections"
docker-compose logs backend   # Should show Uvicorn running on port 8000
```

## Step 3: Backend Setup

### Option A: Using Docker (Recommended)

The backend runs automatically in Docker. Just verify it's working:

```bash
# Check health
curl http://localhost:8000/health

# Visit API docs
# Open browser: http://localhost:8000/docs
```

### Option B: Local Python Installation

If you prefer to run FastAPI locally:

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (when Alembic is set up)
# python -m alembic upgrade head

# Start server
uvicorn app.main:app --reload

# API will be available at http://localhost:8000
```

## Step 4: Frontend Setup

```bash
cd frontend

# Install dependencies (takes 1-2 minutes)
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

## Step 5: Verify Everything Works

### Backend Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Response should be:
# {"status":"healthy","service":"viral-video-saas-api"}

# View API documentation
# Open browser: http://localhost:8000/docs
```

### Frontend Check

```bash
# Open in browser: http://localhost:3000
# Should see landing page with pricing table
```

### Database Check

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d viral_db -c "SELECT 1;"

# Or use Docker:
docker-compose exec postgres psql -U postgres -d viral_db -c "SELECT version();"
```

## Development Workflow

### Making Changes

1. **Backend changes**: Edit `backend/app/` files
   - Changes auto-reload in Docker
   - Check logs: `docker-compose logs backend`

2. **Frontend changes**: Edit `frontend/src/` files
   - Changes auto-reload in dev server
   - Check terminal where `npm run dev` is running

3. **Database changes**: 
   - Update `backend/app/models/` files
   - No migrations set up yet - models auto-create tables on startup

### Running Tests

```bash
# Backend tests
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run tests with coverage report
pytest tests/ --cov=app --cov-report=html

# Frontend linting
cd frontend
npm run lint

# Frontend type checking
npm run type-check
```

### Testing Workflow

1. **Setup test database** (automatic via SQLite in-memory)
2. **Run tests**: `pytest tests/ -v`
3. **Check coverage**: `pytest tests/ --cov=app`
4. **Fix issues** and rerun

Test fixtures available:
- `client`: FastAPI TestClient
- `db`: Database session  
- `db_user`: Test user with email test@example.com
- `token`: Valid JWT token for test user

### Database Operations

```bash
# Connect to database directly
docker-compose exec postgres psql -U postgres -d viral_db

# Common commands:
# \dt                          - List tables
# \d users                      - Describe users table
# SELECT * FROM users;          - View all users
# \q                            - Exit

# Or use SQLAlchemy to query
cd backend
python
>>> from app.database import SessionLocal
>>> db = SessionLocal()
>>> from app.models.user import User
>>> users = db.query(User).all()
>>> for u in users:
...     print(u.email)
```

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove data (WARNING: deletes database)
docker-compose down -v

# Stop just the backend
docker-compose stop backend

# Restart all services
docker-compose restart
```

## Troubleshooting

### Port Already in Use

```bash
# If port 8000 is in use (FastAPI)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# If port 3000 is in use (Next.js)
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# If port 5432 is in use (PostgreSQL)
netstat -ano | findstr :5432
# Use different port or kill process
```

### Docker Service Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check Docker status
docker info
docker ps
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Reset PostgreSQL (WARNING: deletes data)
docker-compose down -v
docker-compose up -d postgres
```

### Frontend Can't Connect to Backend

1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS is configured in `backend/app/main.py`
3. Check `frontend/.env.local` has correct API URL
4. Clear browser cache and restart dev server

### Dependencies Issues

```bash
# Backend dependency conflict
cd backend
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Frontend dependency conflict
cd frontend
rm -r node_modules
npm cache clean --force
npm install
```

## Environment Variables

### Backend (.env)

Key variables to set:

```env
# Development
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/viral_db

# Redis
REDIS_URL=redis://localhost:6379/0

# APIs (get keys from respective services)
STRIPE_SECRET_KEY=sk_test_...
KLING_API_KEY=your-key-here
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Next Steps

1. ✅ Local setup complete
2. Create your first user (visit http://localhost:3000/auth/signup)
3. Test auth endpoints (POST /auth/signup, /auth/login)
4. Build video API endpoint
5. Integrate Kling 3.0 API
6. Implement Stripe payments
7. Deploy to AWS

## Getting Help

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Backend Logs**: `docker-compose logs backend -f`
- **Frontend Logs**: Terminal where `npm run dev` is running
- **Database**: `docker-compose exec postgres psql -U postgres -d viral_db`

## Common Commands Cheatsheet

```bash
# Docker
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f            # View all logs
docker-compose logs backend       # View specific service logs
docker-compose exec postgres psql -U postgres  # Connect to DB

# Backend
cd backend && pip install -r requirements.txt  # Install deps
python -m pytest tests/           # Run tests
uvicorn app.main:app --reload     # Run locally

# Frontend
cd frontend && npm install        # Install deps
npm run dev                       # Start dev server
npm run build                     # Production build
npm run lint                      # Check code quality
```

---

Need more help? Check [README.md](../README.md) or [DEPLOYMENT.md](./DEPLOYMENT.md)
