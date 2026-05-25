# Production Readiness Checklist

Complete verification before deploying Viral Video SaaS to production.

## Pre-Deployment Testing (PHASE 1)

### Unit Tests
- [ ] Run: `pytest backend/tests/ -v`
- [ ] Coverage > 80%: `pytest backend/tests/ --cov=app`
- [ ] All auth tests pass
- [ ] All user endpoint tests pass
- [ ] All payment tests pass
- [ ] All template tests pass
- [ ] All video tests pass

### Integration Tests
- [ ] Test complete video creation flow:
  1. User signup
  2. View templates
  3. Upload image
  4. Create video (charges credits)
  5. Poll status
  6. Download video
- [ ] Test payment flow:
  1. Get packages
  2. Create checkout
  3. Simulate Stripe payment (test card: 4242 4242 4242 4242)
  4. Credits updated
- [ ] Test credit system:
  1. Video cost calculated correctly
  2. Insufficient credits → 402 error
  3. Credit transaction logged
  4. Refund on delete (if <1 hour)

### API Tests (Manual with cURL)
```bash
# Auth flow
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test"}'

# Get token from response, then:
export TOKEN="eyJ0eXAi..."

# User endpoints
curl -X GET http://localhost:8000/api/v1/user \
  -H "Authorization: Bearer $TOKEN"

# Templates
curl -X GET http://localhost:8000/api/v1/templates

# Payments
curl -X GET http://localhost:8000/api/v1/payments/packages \
  -H "Authorization: Bearer $TOKEN"

# Video creation
curl -X POST http://localhost:8000/api/v1/videos \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@test.jpg" \
  -F "title=Test" \
  -F "script=Test script" \
  -F "duration=15"
```

### Frontend Tests
- [ ] Landing page loads without errors
- [ ] Auth pages work (signup/login redirect correctly)
- [ ] Create video form:
  - [ ] Image upload works
  - [ ] Form validation works
  - [ ] Submit creates video
  - [ ] Error messages show
- [ ] Video library loads
- [ ] Account page displays:
  - [ ] Current credits
  - [ ] Transaction history
  - [ ] User profile info
- [ ] Billing page:
  - [ ] Package options visible
  - [ ] Checkout redirects to Stripe
  - [ ] Stripe payment works

---

## Environment & Configuration (PHASE 2)

### Backend Configuration
- [ ] `.env` file has all required variables:
  - [ ] `SECRET_KEY` - Strong random string (generate: `openssl rand -hex 32`)
  - [ ] `DATABASE_URL` - Points to RDS (not localhost)
  - [ ] `REDIS_URL` - Points to ElastiCache
  - [ ] `STRIPE_SECRET_KEY` - Live key (sk_live_*)
  - [ ] `KLING_API_KEY` - Valid Kling API key
  - [ ] `AWS_ACCESS_KEY_ID` - IAM credentials
  - [ ] `AWS_SECRET_ACCESS_KEY` - IAM secret
  - [ ] `AWS_REGION` - us-east-1 (or your region)
  - [ ] `S3_BUCKET_VIDEOS` - Production bucket name
  - [ ] `S3_BUCKET_UPLOADS` - Production bucket name
  - [ ] `DEBUG` - Set to False in production
- [ ] Store secrets in AWS Secrets Manager (not in code)
- [ ] CORS origins updated:
  - [ ] Production domain added (e.g., https://viral-video.app)
  - [ ] localhost removed (or only in dev)

### Frontend Configuration
- [ ] `.env.production` has:
  - [ ] `NEXT_PUBLIC_API_URL` - Points to production API
  - [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Live key (pk_live_*)
- [ ] No localhost URLs in production build
- [ ] Build command works: `npm run build`
- [ ] Production build is optimized

### Database Configuration
- [ ] RDS PostgreSQL instance running
- [ ] Database initialized with schema:
  ```bash
  # Via Alembic migrations (if set up)
  alembic upgrade head
  
  # Or manual via app startup (models auto-create)
  ```
- [ ] Tables created:
  - [ ] users
  - [ ] videos
  - [ ] credit_transactions
  - [ ] video_templates
  - [ ] payments
- [ ] Backups enabled (7-day retention)
- [ ] Read replica configured (optional but recommended)

### Redis Configuration
- [ ] ElastiCache Redis cluster running
- [ ] Celery broker points to Redis
- [ ] Connection test successful:
  ```bash
  redis-cli -h redis-endpoint ping
  # Should return: PONG
  ```

### S3 Configuration
- [ ] Two S3 buckets created:
  - [ ] `viral-videos-{account-id}` - For generated videos
  - [ ] `viral-uploads-{account-id}` - For user uploads
- [ ] Bucket policies configured for:
  - [ ] CloudFront access (GET)
  - [ ] Application access (PUT/GET/DELETE)
  - [ ] No public access (private)
- [ ] Lifecycle policy configured:
  - [ ] Delete objects after 7 days
  - [ ] Archive to Glacier after 30 days (optional)

### CloudFront Configuration
- [ ] CloudFront distribution created
- [ ] Origin: S3 bucket for videos
- [ ] Cache behavior configured:
  - [ ] TTL: 1 day for videos
  - [ ] TTL: 5 minutes for API responses
- [ ] HTTPS enforced (redirect HTTP → HTTPS)
- [ ] Custom domain: videos.viral-video.app (optional)

### DNS/Domain Configuration
- [ ] Domain registered (viral-video.app)
- [ ] DNS records:
  - [ ] CNAME: api.viral-video.app → ALB DNS name
  - [ ] CNAME: www.viral-video.app → CloudFront domain
  - [ ] MX records (if using email)
  - [ ] TXT records (SPF, DKIM if needed)
- [ ] SSL certificate provisioned (ACM)
- [ ] HTTPS working on all endpoints

---

## AWS Infrastructure (PHASE 3)

### ECS & Fargate
- [ ] ECS cluster created
- [ ] ECR repositories created:
  - [ ] viral-backend
  - [ ] viral-frontend
- [ ] Task definitions registered:
  - [ ] backend task definition
  - [ ] frontend task definition
- [ ] Fargate services running:
  - [ ] backend service (2+ tasks)
  - [ ] frontend service (2+ tasks)
- [ ] Auto-scaling configured:
  - [ ] Min: 2 tasks
  - [ ] Max: 5 tasks
  - [ ] Scale on CPU > 70%

### Load Balancer
- [ ] Application Load Balancer created
- [ ] Health checks configured:
  - [ ] Backend: /health
  - [ ] Frontend: /
- [ ] Target groups created
- [ ] Listeners configured:
  - [ ] 80 → 443 redirect
  - [ ] 443 → targets (HTTPS)
- [ ] Security group allows:
  - [ ] 80, 443 from internet
  - [ ] 5432 (RDS) from ECS
  - [ ] 6379 (Redis) from ECS

### RDS Database
- [ ] RDS instance provisioned:
  - [ ] Engine: PostgreSQL 15.3
  - [ ] Instance class: db.t3.micro (or larger for prod)
  - [ ] Storage: 20GB (auto-scale enabled)
- [ ] Multi-AZ enabled
- [ ] Backup retention: 7 days
- [ ] Enhanced monitoring enabled
- [ ] Parameter groups optimized
- [ ] Database migration ran successfully:
  ```bash
  psql -h prod-db.rds.amazonaws.com -U postgres -d viral_db
  \dt  # Should show all tables
  ```

### ElastiCache Redis
- [ ] Redis cluster created:
  - [ ] Node type: cache.t3.micro
  - [ ] Engine version: 7.0
  - [ ] Multi-AZ enabled
- [ ] Security group allows ECS access
- [ ] Backup enabled
- [ ] Parameter groups configured

### CloudWatch Monitoring
- [ ] Log groups created:
  - [ ] /ecs/viral-backend
  - [ ] /ecs/viral-frontend
- [ ] Alarms configured:
  - [ ] High CPU (>80%)
  - [ ] High memory (>80%)
  - [ ] High error rate (>5%)
  - [ ] Health check failures
- [ ] Dashboards created for monitoring

---

## Security Verification (PHASE 4)

### Secrets Management
- [ ] All sensitive data in AWS Secrets Manager:
  - [ ] Database password
  - [ ] Stripe API keys
  - [ ] Kling API key
  - [ ] JWT secret key
- [ ] No secrets in Docker images
- [ ] No secrets in git history
- [ ] .env files in .gitignore
- [ ] Rotation policy configured

### API Security
- [ ] HTTPS enforced (redirect HTTP → HTTPS)
- [ ] CORS correctly configured:
  - [ ] Only production domain allowed
  - [ ] Credentials allowed
- [ ] Rate limiting implemented:
  - [ ] 100 requests/minute per user
  - [ ] 10 concurrent video generations
- [ ] SQL injection prevention (SQLAlchemy parameterized)
- [ ] XSS prevention (sanitize inputs)
- [ ] CSRF protection on forms
- [ ] API key validation for Stripe/Kling webhooks

### Infrastructure Security
- [ ] Security groups properly configured:
  - [ ] No open ports except 80/443
  - [ ] Database only accessible from app
  - [ ] Redis only accessible from app
- [ ] IAM roles with least privilege:
  - [ ] ECS task role (S3, Secrets Manager)
  - [ ] CI/CD role (ECR push, CloudFormation)
- [ ] VPC endpoints for AWS services (optional but recommended)
- [ ] WAF rules configured (optional)

### Data Protection
- [ ] Data encrypted at rest (RDS, S3)
- [ ] Data encrypted in transit (TLS 1.2+)
- [ ] Backup encrypted
- [ ] Database password complexity enforced
- [ ] User passwords hashed (bcrypt)
- [ ] Credit transactions audited

---

## Performance & Optimization (PHASE 5)

### Backend Performance
- [ ] API response time < 200ms (p95):
  ```bash
  # Test with Apache Bench
  ab -n 1000 -c 10 https://api.viral-video.app/health
  ```
- [ ] Database queries optimized:
  - [ ] Indexes created on foreign keys
  - [ ] N+1 queries eliminated
  - [ ] Query timeouts set
- [ ] Caching implemented:
  - [ ] Redis used for session data
  - [ ] Video metadata cached
- [ ] Connection pooling configured
- [ ] Database connection limits set

### Frontend Performance
- [ ] Lighthouse score > 90:
  ```bash
  npm run build  # Production build
  npm run start  # Verify production
  ```
- [ ] Images optimized (Next.js Image)
- [ ] Code splitting configured
- [ ] Bundle size < 500KB (gzip)
- [ ] CSS/JS minified
- [ ] CDN serving static assets

### Video Processing
- [ ] Video generation time logged
- [ ] Average generation: < 2 minutes
- [ ] Timeout handling: 5 minutes max
- [ ] Retry logic for failed videos
- [ ] Celery task monitoring

---

## Monitoring & Alerting (PHASE 6)

### Application Monitoring
- [ ] DataDog or equivalent installed
- [ ] Key metrics monitored:
  - [ ] API latency
  - [ ] Error rate
  - [ ] Active users
  - [ ] Video generation success rate
  - [ ] Credit transactions
- [ ] Alerts configured:
  - [ ] Email/SMS on critical errors
  - [ ] PagerDuty integration (if available)
  - [ ] Slack notifications

### Logging
- [ ] Structured logging enabled:
  - [ ] All requests logged
  - [ ] Error stack traces captured
  - [ ] Performance metrics logged
- [ ] Log retention: 30 days
- [ ] Log aggregation: CloudWatch or DataDog
- [ ] Search capabilities working

### Error Tracking
- [ ] Sentry or equivalent configured
- [ ] Error notifications sent
- [ ] Release tracking enabled
- [ ] Source maps uploaded

---

## Data Verification (PHASE 7)

### Database Validation
```sql
-- Check users table
SELECT COUNT(*) as user_count FROM users;

-- Check videos table
SELECT COUNT(*) as video_count FROM videos;

-- Check credit transactions
SELECT COUNT(*) as txn_count FROM credit_transactions;

-- Check templates
SELECT COUNT(*) as template_count FROM video_templates;

-- Check sum of credits
SELECT SUM(credits_balance) as total_credits FROM users;
```

### File Storage Verification
```bash
# Check S3 videos bucket
aws s3 ls s3://viral-videos-123456789/ --recursive --human-readable

# Check S3 uploads bucket
aws s3 ls s3://viral-uploads-123456789/ --recursive --human-readable

# Test CloudFront
curl -I https://videos.viral-video.app/sample-video.mp4
```

---

## Deployment Validation (PHASE 8)

### End-to-End Flow Test
1. [ ] Create new user account
2. [ ] View templates (verify 20+ templates)
3. [ ] Generate video:
   - [ ] Upload image
   - [ ] Select template
   - [ ] Enter text
   - [ ] Check credits available
   - [ ] Submit generation
4. [ ] Monitor video creation:
   - [ ] Status updates in real-time
   - [ ] Progress visible
5. [ ] Download completed video:
   - [ ] File downloads
   - [ ] Plays correctly
6. [ ] Purchase credits:
   - [ ] View packages
   - [ ] Stripe checkout works
   - [ ] Credits updated after payment
7. [ ] Delete video:
   - [ ] Deleted successfully
   - [ ] Credits refunded (if <1 hour)

### Load Testing (Optional)
```bash
# Install k6 or Apache Bench
# Test API endpoints under load
k6 run load-test.js

# Expected results:
# - p95 latency < 500ms
# - 95th percentile < 1s
# - Error rate < 1%
```

---

## Documentation & Handoff (PHASE 9)

### Documentation Complete
- [ ] API documentation updated
- [ ] Architecture documentation created
- [ ] Deployment guide comprehensive
- [ ] Local setup guide updated
- [ ] Troubleshooting guide created
- [ ] Runbook for on-call created

### Code Quality
- [ ] All code reviewed
- [ ] No TODO/FIXME comments left
- [ ] Comments updated
- [ ] Docstrings complete
- [ ] Type hints added

### Knowledge Transfer
- [ ] Team trained on system
- [ ] Deployment process documented
- [ ] Emergency procedures documented
- [ ] Escalation paths clear

---

## Go-Live Checklist (FINAL)

### Pre-Launch (24 hours before)
- [ ] All tests passing
- [ ] Monitoring verified
- [ ] Backup confirmed
- [ ] Rollback plan ready
- [ ] Team available for support

### Launch Day
- [ ] Final database backup taken
- [ ] Monitoring active
- [ ] Team on standby
- [ ] Marketing ready to announce
- [ ] Status page updated

### Post-Launch (First 24 hours)
- [ ] Monitor error rate (should be <0.5%)
- [ ] Monitor latency (should be <200ms p95)
- [ ] Check daily active users
- [ ] Monitor Stripe payments
- [ ] Gather initial user feedback
- [ ] Fix any critical issues

### Week 1
- [ ] Monitor churn rate
- [ ] Check user retention
- [ ] Review usage patterns
- [ ] Optimize based on data
- [ ] Plan next features

---

## Rollback Plan

If critical issues found:

1. **Immediate Actions**
   - Disable affected feature via flag
   - Scale down traffic if needed
   - Alert on-call team

2. **Rollback Steps**
   ```bash
   # Revert to previous image
   docker tag viral-backend:previous-version 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-backend:latest
   docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-backend:latest
   
   # Force new deployment
   aws ecs update-service \
     --cluster viral-video-prod \
     --service viral-backend \
     --force-new-deployment
   ```

3. **Verification**
   - Health checks passing
   - Error rate normal
   - Users can use platform

---

**Status**: Ready for Production
**Last Review**: May 24, 2026
**Next Review**: June 1, 2026 (Post-launch)
