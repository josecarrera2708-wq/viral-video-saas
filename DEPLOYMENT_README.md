# Deployment Guide - Viral Video SaaS

**Status**: Ready to Deploy
**Environment**: AWS (Fargate, RDS, ElastiCache, S3, CloudFront)
**Estimated Time**: 5-7 days (1-2 of which is AWS processing)
**Estimated Cost**: $140-170/month

---

## Quick Start Deployment Options

### Option 1: Automated Deployment (Recommended)
**Time**: 30 minutes hands-on + AWS processing time
**Difficulty**: Easy

```bash
# Verify everything is ready
./verify-deployment-ready.sh

# Get AWS credentials ready
aws configure

# Run automated deployment
./deploy.sh all

# Validate deployment
./post-deployment-validation.sh
```

**Files Used**:
- `deploy.sh` - Automated deployment script
- `infrastructure/terraform.tfvars.example` → copy to `terraform.tfvars`

**See**: [SPRINT4_DEPLOYMENT.md](./SPRINT4_DEPLOYMENT.md) Phase 1-7

---

### Option 2: Manual Deployment
**Time**: 2-3 hours hands-on + AWS processing
**Difficulty**: Medium

Follow step-by-step instructions to understand each part of deployment.

```bash
# Read complete instructions
cat MANUAL_DEPLOYMENT.md

# Follow each section in order
# Each step includes AWS CLI commands with explanations
```

**See**: [MANUAL_DEPLOYMENT.md](./MANUAL_DEPLOYMENT.md)

---

### Option 3: Terraform Only (For Infrastructure Team)
**Time**: 45 minutes + AWS processing
**Difficulty**: Easy

```bash
cd infrastructure

# Setup variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Plan and apply
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Get outputs
terraform output
```

**See**: [infrastructure/](./infrastructure/) directory

---

## Pre-Deployment Checklist

### 1. Verify Code is Ready
```bash
./verify-deployment-ready.sh
```

Must pass all checks before proceeding.

### 2. Get Required Credentials

- **AWS Account**: Free tier available, or existing account
- **Stripe API Keys**:
  - Test: `sk_test_...` and `pk_test_...` (free)
  - Production: `sk_live_...` and `pk_live_...` (after approval)
- **Kling API Key**: Request at https://kling.kuaishou.com/api
- **Domain Name**: Buy from domain registrar (optional, use AWS URL initially)
- **AWS IAM User**: Create with ECR, RDS, ECS, S3, CloudFront, VPC permissions

### 3. Configure Environment Files

```bash
cd infrastructure

# Copy template
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
# - AWS region (default: us-east-1)
# - Database password (generate with: openssl rand -base64 32)
# - Instance sizes (default: micro/t3.micro for cost)
```

### 4. Prepare Secrets

```bash
# Generate secure random keys
openssl rand -base64 32  # For SECRET_KEY
openssl rand -hex 32     # Alternative format

# Have these ready:
# - STRIPE_SECRET_KEY (from Stripe dashboard)
# - KLING_API_KEY (from Kling API console)
# - AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY (from IAM user)
# - ELEVENLABS_API_KEY (optional, from ElevenLabs)
```

---

## Deployment Steps Overview

### PHASE 1: AWS Setup (30 min - 1 hour)
- [ ] Create/verify AWS account
- [ ] Create IAM user with required permissions
- [ ] Configure AWS CLI: `aws configure`
- [ ] Get AWS Account ID: `aws sts get-caller-identity`
- [ ] Create ECR repositories (for Docker images)
- [ ] Build and push Docker images to ECR

**Tools**: AWS CLI, Docker

### PHASE 2: Infrastructure Deployment (30 min active + 10-15 min AWS)
- [ ] Initialize Terraform: `terraform init`
- [ ] Plan infrastructure: `terraform plan -out=tfplan`
- [ ] Apply infrastructure: `terraform apply tfplan`
- [ ] Save outputs: `terraform output`

**Terraform Creates**:
- VPC with public/private subnets
- RDS PostgreSQL (multi-AZ)
- ElastiCache Redis
- S3 buckets (videos, uploads)
- Security groups & IAM roles
- CloudWatch log groups

**Tools**: Terraform

### PHASE 3: Service Configuration (30 min)
- [ ] Create ECS cluster
- [ ] Register task definitions
- [ ] Create ECS services (Fargate)
- [ ] Setup Application Load Balancer
- [ ] Configure auto-scaling

**Tools**: AWS CLI, ECS console

### PHASE 4: Database & Storage (15 min)
- [ ] Initialize RDS database
- [ ] Create database schema (auto-created by app)
- [ ] Configure S3 buckets
- [ ] Setup CloudFront CDN
- [ ] Configure lifecycle policies

**Tools**: psql, AWS CLI, AWS Console

### PHASE 5: Security & DNS (30 min)
- [ ] Request SSL/TLS certificate (ACM)
- [ ] Configure Route53 DNS (or update domain registrar)
- [ ] Setup ALB listeners with HTTPS
- [ ] Configure CORS headers
- [ ] Create IAM policies

**Tools**: AWS ACM, Route53, AWS Console

### PHASE 6: Monitoring & Logging (20 min)
- [ ] Create CloudWatch log groups
- [ ] Setup CloudWatch alarms
- [ ] Configure application logging
- [ ] Setup error tracking (Sentry)
- [ ] Setup performance monitoring (DataDog)

**Tools**: CloudWatch, Sentry, DataDog

### PHASE 7: Validation (20 min)
- [ ] Run health checks
- [ ] Test API endpoints
- [ ] Test frontend loading
- [ ] Verify database connectivity
- [ ] Check monitoring is working

**Tools**: `post-deployment-validation.sh`, curl, AWS Console

---

## Full Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| Pre-deployment setup | 1-2 hours | Get credentials, verify code |
| Phase 1: AWS Setup | 30 min | IAM, ECR, Docker |
| Phase 2: Infrastructure | 30 min active + 10-15 min AWS | Terraform |
| Phase 3: Services | 30 min | ECS, ALB, auto-scaling |
| Phase 4: Database | 15 min | RDS, S3, CloudFront |
| Phase 5: Security | 30 min | SSL/TLS, DNS, CORS |
| Phase 6: Monitoring | 20 min | CloudWatch, alarms |
| Phase 7: Validation | 20 min | Health checks |
| **Total** | **4-6 hours active + 1-2 days AWS waiting** | Ready for beta test |

**Critical Path**:
- AWS setup → Terraform (10-15 min waiting for RDS)
- Services → ALB needs certificate (5-30 min validation wait)
- Everything else can happen in parallel

**Fastest deployment**: ~3 hours active work

---

## Deployment Tools Comparison

### Option 1: Automated (deploy.sh)
```
Pros:
✓ Fastest (~30 min hands-on)
✓ Error handling built-in
✓ Less room for mistakes
✓ Repeatable

Cons:
✗ Less transparent
✗ Harder to debug if something fails
✗ Less customization
```

### Option 2: Manual Step-by-Step
```
Pros:
✓ Full control
✓ Understand each step
✓ Easy to customize
✓ Good for learning

Cons:
✗ Slower (~2-3 hours)
✗ More room for mistakes
✗ Requires AWS CLI knowledge
```

### Option 3: Terraform Only
```
Pros:
✓ Fast for infrastructure
✓ Reproducible
✓ Easy to modify
✓ Infrastructure-as-Code

Cons:
✗ Still need manual service creation
✗ Requires Terraform knowledge
✗ Need to push Docker images manually
```

**Recommendation**: Start with **Option 1 (Automated)**, and if something breaks, use **Option 2 (Manual)** to debug.

---

## Common Issues & Solutions

### Docker Images Won't Push to ECR
**Solution**: 
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

### RDS Takes Too Long
**Normal**: First RDS instance creation takes 10-15 minutes. Monitor in AWS Console.

### Terraform Apply Fails
**Solution**:
1. Check error message carefully
2. Verify credentials: `aws sts get-caller-identity`
3. Check IAM permissions
4. Try again - sometimes transient failures occur

### Services Not Starting
**Solution**:
1. Check task logs: `aws logs tail /ecs/viral-backend --follow`
2. Verify task definition: `aws ecs describe-task-definition --task-definition viral-backend:1`
3. Check security groups allow 8000
4. Verify secrets are created in Secrets Manager

### Database Connection Fails
**Solution**:
1. Verify RDS endpoint: `terraform output rds_endpoint`
2. Check security group: `aws ec2 describe-security-groups --group-ids sg-xxxxx`
3. Ensure port 5432 is open from ECS security group
4. Test manually: `psql -h <endpoint> -U postgres`

---

## After Deployment

### Day 1: Validation
- [ ] Run `./post-deployment-validation.sh`
- [ ] Test API endpoints manually
- [ ] Check CloudWatch logs for errors
- [ ] Verify HTTPS/SSL working

### Day 2-3: Internal Testing
- [ ] Test signup/login flow
- [ ] Test video creation (with valid Kling API key)
- [ ] Test payment flow (with Stripe test card)
- [ ] Test video download and playback
- [ ] Monitor resource utilization

### Day 4-5: Beta Launch Preparation
- [ ] Finalize monitoring and alerts
- [ ] Create support runbook
- [ ] Prepare beta user communications
- [ ] Setup analytics tracking (optional)

### Day 5+: Soft Launch
- [ ] Invite 50 beta testers
- [ ] Monitor metrics closely
- [ ] Fix critical bugs
- [ ] Gather feedback
- [ ] Plan GA launch

---

## Deployment Rollback

If critical issues are found:

### Quick Rollback (Scale Down)
```bash
# Temporarily disable service
aws ecs update-service \
  --cluster viral-video-prod \
  --service viral-backend \
  --desired-count 0
```

### Full Rollback (Infrastructure)
```bash
cd infrastructure

# Destroy all resources
terraform destroy

# This will delete:
# - VPC and subnets
# - RDS database (backup created first)
# - Redis cluster
# - S3 buckets
# - All security groups
```

---

## Cost Estimation

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| ECS Fargate | $30-50 | 2 tasks, 0.5 vCPU, 512MB RAM |
| RDS PostgreSQL | $40-50 | db.t3.micro, 20GB storage |
| ElastiCache Redis | $20 | cache.t3.micro |
| S3 Storage | $12 | 500GB videos |
| S3 Transfer | $9 | 100GB outbound |
| CloudFront | $8 | 100GB cached |
| ALB | $16 | 730 hours/month |
| Data Transfer | $5 | Cross-AZ |
| **TOTAL** | **$140-170** | Scales with usage |

**To reduce costs**:
- Use smaller instances initially (db.t3.micro is fine for <1000 users)
- Reduce backup retention (7 days is default)
- Use S3 Intelligent-Tiering for old videos
- Monitor CloudFront hit ratio

---

## Success Metrics

After deployment, you should see:
- ✅ API latency < 200ms (p95)
- ✅ 99.5% uptime
- ✅ <1% error rate
- ✅ Database connectivity
- ✅ S3 uploads working
- ✅ SSL/TLS certificates valid
- ✅ CloudWatch logs being collected
- ✅ Auto-scaling triggers configured

---

## Next Steps

1. **Choose your deployment method**:
   - Easy path: `./deploy.sh all`
   - Learning path: `MANUAL_DEPLOYMENT.md`

2. **Gather prerequisites**:
   - AWS account & credentials
   - Stripe API keys
   - Kling API key
   - Domain name (optional)

3. **Run verification**:
   ```bash
   ./verify-deployment-ready.sh
   ```

4. **Start deployment**:
   - Follow your chosen guide
   - Monitor progress in AWS Console
   - Keep logs from all steps

5. **Validate**:
   ```bash
   ./post-deployment-validation.sh
   ```

6. **Soft launch**:
   - Invite 50 beta users
   - Monitor metrics
   - Fix issues
   - GA Launch!

---

## Support & Documentation

| Document | Purpose |
|----------|---------|
| `SPRINT4_DEPLOYMENT.md` | Detailed deployment guide (phases 1-7) |
| `MANUAL_DEPLOYMENT.md` | Step-by-step manual deployment |
| `docs/PRODUCTION_CHECKLIST.md` | Pre-launch validation (9 phases) |
| `post-deployment-validation.sh` | Automated post-deployment tests |
| `deploy.sh` | Automated deployment script |
| `verify-deployment-ready.sh` | Pre-deployment verification |

---

**Status**: ✅ Ready to Deploy
**Confidence Level**: HIGH - All components tested
**Next Action**: Read deployment guide and start!

Choose your deployment method and let's ship this! 🚀
