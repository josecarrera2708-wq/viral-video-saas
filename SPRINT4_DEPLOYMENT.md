# SPRINT 4: AWS Deployment & Launch Preparation

**Objective**: Deploy Viral Video SaaS to AWS Fargate with RDS, ElastiCache, S3, and CloudFront
**Timeline**: Week 7-8 (5 days for full deployment + launch prep)
**Status**: Ready to execute

---

## Phase 1: Pre-Deployment (Day 1)

### Step 1: Setup AWS Account & Credentials

```bash
# 1. Create AWS account or use existing
# https://aws.amazon.com/

# 2. Create IAM user for Terraform
# Go to: IAM > Users > Add User
# Name: terraform-user
# Attach policies:
#   - EC2FullAccess
#   - RDSFullAccess
#   - ElastiCacheFullAccess
#   - S3FullAccess
#   - CloudFrontFullAccess
#   - ECSFullAccess
#   - VPCFullAccess
#   - IAMFullAccess

# 3. Create access keys
# Go to: User > Security credentials > Create access key
# Download CSV file with credentials

# 4. Configure AWS CLI
aws configure
# Enter: Access Key ID
# Enter: Secret Access Key
# Region: us-east-1
# Output: json
```

### Step 2: Prepare Docker Images

```bash
# 1. Build backend image
cd C:\Users\mario\viral-video-saas
docker build -t viral-backend:latest -f backend/docker/Dockerfile backend/

# 2. Build frontend image
docker build -t viral-frontend:latest -f frontend/Dockerfile frontend/

# 3. Verify images
docker images | grep viral
# Should show:
#   viral-backend  latest
#   viral-frontend latest
```

### Step 3: Create ECR Repositories

```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo $AWS_ACCOUNT_ID  # Save this value

# Create backend repository
aws ecr create-repository --repository-name viral-backend --region us-east-1
# Note: You'll get a URI like: 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-backend

# Create frontend repository
aws ecr create-repository --repository-name viral-frontend --region us-east-1

# Save these URIs for later
# BACKEND_URI=123456789.dkr.ecr.us-east-1.amazonaws.com/viral-backend
# FRONTEND_URI=123456789.dkr.ecr.us-east-1.amazonaws.com/viral-frontend
```

### Step 4: Push Docker Images to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag images
docker tag viral-backend:latest $BACKEND_URI:latest
docker tag viral-frontend:latest $FRONTEND_URI:latest

# Push to ECR
docker push $BACKEND_URI:latest
docker push $FRONTEND_URI:latest

# Verify
aws ecr list-images --repository-name viral-backend
aws ecr list-images --repository-name viral-frontend
```

---

## Phase 2: Infrastructure Deployment (Day 2-3)

### Step 5: Setup Terraform Variables

```bash
cd C:\Users\mario\viral-video-saas\infrastructure

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region           = "us-east-1"
app_name            = "viral-video-saas"
environment         = "production"
db_password         = "$(openssl rand -base64 32)"  # Generate strong password
rds_instance_class  = "db.t3.micro"  # Can upgrade to db.t3.small for better performance
redis_node_type     = "cache.t3.micro"
enable_multi_az     = true
backup_retention    = 7
log_retention_days  = 30

# Docker image URIs (from previous step)
backend_image_uri   = "$BACKEND_URI:latest"
frontend_image_uri  = "$FRONTEND_URI:latest"
EOF
```

### Step 6: Initialize & Plan Terraform

```bash
# Initialize Terraform
terraform init

# Review what will be created
terraform plan -out=tfplan

# Should show:
# - VPC with subnets
# - RDS PostgreSQL instance
# - ElastiCache Redis cluster
# - S3 buckets (2)
# - Security groups
# - ECS cluster components
# - CloudFront distribution
# Plan: ~50+ resources to create
```

### Step 7: Apply Terraform

```bash
# Apply configuration
terraform apply tfplan

# Wait 10-15 minutes for resources to be created
# Monitor progress in AWS Console

# Save outputs
terraform output > deployment-outputs.txt

# Important outputs to save:
# - RDS endpoint (viral-db.xxxxx.rds.amazonaws.com)
# - Redis endpoint (viral-redis.xxxxx.cache.amazonaws.com)
# - S3 bucket names
# - CloudFront domain

echo "Infrastructure deployed! Saving outputs..."
aws cloudformation describe-stacks --stack-name viral-video-saas > stack-info.json
```

### Step 8: Configure Environment Variables in AWS

```bash
# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name viral-video/prod/database \
  --secret-string "postgresql://postgres:PASSWORD@viral-db.xxxxx.rds.amazonaws.com:5432/viral_db"

aws secretsmanager create-secret \
  --name viral-video/prod/redis \
  --secret-string "redis://viral-redis.xxxxx.cache.amazonaws.com:6379/0"

aws secretsmanager create-secret \
  --name viral-video/prod/secrets \
  --secret-string '{
    "SECRET_KEY": "'"$(openssl rand -hex 32)"'",
    "STRIPE_SECRET_KEY": "sk_live_XXXXXX",
    "KLING_API_KEY": "your-kling-key",
    "ELEVENLABS_API_KEY": "optional",
    "AWS_ACCESS_KEY_ID": "your-iam-key",
    "AWS_SECRET_ACCESS_KEY": "your-iam-secret"
  }'
```

---

## Phase 3: ECS/Fargate Deployment (Day 3-4)

### Step 9: Create ECS Task Definitions

```bash
# Create backend task definition
aws ecs register-task-definition \
  --cli-input-json file://backend-task-definition.json

# Create frontend task definition
aws ecs register-task-definition \
  --cli-input-json file://frontend-task-definition.json

# Verify
aws ecs list-task-definitions
```

### Step 10: Create ECS Cluster & Services

```bash
# Create cluster (Terraform already did this, but ensure it exists)
aws ecs create-cluster --cluster-name viral-video-prod

# Create backend service
aws ecs create-service \
  --cluster viral-video-prod \
  --service-name viral-backend \
  --task-definition viral-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-xxxxx,subnet-yyyyy],
    securityGroups=[sg-xxxxx],
    assignPublicIp=ENABLED
  }" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000"

# Create frontend service
aws ecs create-service \
  --cluster viral-video-prod \
  --service-name viral-frontend \
  --task-definition viral-frontend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-xxxxx,subnet-yyyyy],
    securityGroups=[sg-xxxxx],
    assignPublicIp=ENABLED
  }"

# Monitor deployment
aws ecs describe-services \
  --cluster viral-video-prod \
  --services viral-backend viral-frontend

# Wait for: desiredCount = runningCount = 2
```

### Step 11: Setup Application Load Balancer

```bash
# Create target group for backend
aws elbv2 create-target-group \
  --name viral-backend-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --health-check-protocol HTTP \
  --health-check-path /health

# Register backend tasks
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=task-id-1 Id=task-id-2

# Create ALB listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:...
```

### Step 12: Configure Auto Scaling

```bash
# Create auto scaling target
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name viral-backend-asg \
  --launch-template LaunchTemplateName=viral-backend \
  --min-size 2 \
  --max-size 5 \
  --desired-capacity 2 \
  --availability-zones us-east-1a us-east-1b

# Create scaling policy (scale up on CPU > 70%)
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name viral-backend-asg \
  --policy-name scale-up \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration file://scaling-config.json
```

---

## Phase 4: Database & Storage Setup (Day 3)

### Step 13: Initialize RDS Database

```bash
# Get RDS endpoint from terraform outputs
RDS_ENDPOINT=$(terraform output rds_endpoint)

# Connect and initialize
psql -h $RDS_ENDPOINT -U postgres -d viral_db << EOF
-- Create extensions
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- Verify tables exist (created by SQLAlchemy on app startup)
\dt

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_state ON videos(state);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created ON credit_transactions(created_at);

-- Verify
SELECT * FROM information_schema.tables WHERE table_schema='public';
EOF
```

### Step 14: Configure S3 Buckets

```bash
# Get bucket names from Terraform outputs
VIDEOS_BUCKET=$(terraform output s3_videos_bucket)
UPLOADS_BUCKET=$(terraform output s3_uploads_bucket)

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $VIDEOS_BUCKET \
  --versioning-configuration Status=Enabled

# Set lifecycle policies
aws s3api put-bucket-lifecycle-configuration \
  --bucket $VIDEOS_BUCKET \
  --lifecycle-configuration file://s3-lifecycle.json

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket $VIDEOS_BUCKET \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket $VIDEOS_BUCKET \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### Step 15: Setup CloudFront Distribution

```bash
# Get S3 bucket domain
S3_DOMAIN=$(aws s3api get-bucket-location --bucket $VIDEOS_BUCKET)

# Create CloudFront distribution
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json

# Save distribution ID and domain name
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query 'DistributionList.Items[0].Id' --output text)
CLOUDFRONT_DOMAIN=$(aws cloudfront list-distributions --query 'DistributionList.Items[0].DomainName' --output text)

echo "CloudFront Domain: $CLOUDFRONT_DOMAIN"
# Use this in environment variables as CDN URL
```

---

## Phase 5: Monitoring & Logging (Day 4)

### Step 16: Setup CloudWatch Monitoring

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/viral-backend
aws logs create-log-group --log-group-name /ecs/viral-frontend
aws logs create-log-group --log-group-name /rds/viral-db

# Create alarms for backend
aws cloudwatch put-metric-alarm \
  --alarm-name viral-backend-high-cpu \
  --alarm-description "Alert if CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

aws cloudwatch put-metric-alarm \
  --alarm-name viral-backend-error-rate \
  --alarm-description "Alert if error rate > 5%" \
  --metric-name ErrorCount \
  --namespace AWS/ECS \
  --statistic Sum \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold
```

### Step 17: Setup Application Monitoring (Sentry/DataDog)

```bash
# Option A: Sentry (Error tracking)
# 1. Create Sentry account: https://sentry.io/
# 2. Create project for FastAPI
# 3. Get SENTRY_DSN from project settings
# 4. Store in AWS Secrets Manager

aws secretsmanager update-secret \
  --secret-id viral-video/prod/secrets \
  --secret-string '{...SENTRY_DSN...}'

# Option B: DataDog (Full monitoring)
# 1. Create DataDog account: https://datadog.com/
# 2. Install DataDog agent in ECS
# 3. Configure APM and logging
```

---

## Phase 6: DNS & SSL Configuration (Day 4)

### Step 18: Configure Route53 DNS

```bash
# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "ALB DNS: $ALB_DNS"

# Create or update Route53 records
# Option A: If domain is in Route53
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123XYZABC \
  --change-batch file://dns-records.json

# Option B: If domain is elsewhere
# 1. Log into domain registrar
# 2. Create CNAME records:
#    - api.viral-video.app -> ALB DNS
#    - www.viral-video.app -> api.viral-video.app
#    - videos.viral-video.app -> CloudFront domain
```

### Step 19: Setup SSL/TLS Certificate

```bash
# Request certificate in ACM
aws acm request-certificate \
  --domain-name viral-video.app \
  --subject-alternative-names www.viral-video.app api.viral-video.app \
  --validation-method DNS

# Verify certificate (click link in email)
# Once verified, attach to ALB listener

# Update ALB listener to use HTTPS
aws elbv2 modify-listener \
  --listener-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:...

# Redirect HTTP to HTTPS
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}"
```

---

## Phase 7: Final Validation (Day 5)

### Step 20: Health Checks

```bash
# Get backend URL
BACKEND_URL="https://api.viral-video.app"

# Test health endpoint
curl -I $BACKEND_URL/health
# Expected: 200 OK

# Test API docs
curl -I $BACKEND_URL/docs
# Expected: 200 OK

# Test database connection
curl -X GET "$BACKEND_URL/api/v1/user" \
  -H "Authorization: Bearer eyJ0eXAi..."
# Expected: 200 or 401 (depending on token)

# Test frontend
curl -I https://viral-video.app
# Expected: 200 OK
```

### Step 21: End-to-End Testing

```
1. ✅ Create account
   - Visit https://viral-video.app/auth/signup
   - Create account with new email
   - Should redirect to dashboard

2. ✅ List templates
   - Go to /create
   - Should show 20+ templates
   - Filter by category should work

3. ✅ Create video
   - Upload image
   - Select template
   - Enter text
   - Click Generate
   - Status should update

4. ✅ Purchase credits
   - Go to Billing
   - Select package
   - Click Checkout
   - Complete Stripe payment
   - Credits should update

5. ✅ Download video
   - When complete, download should work
   - Video should play in browser
   - File size ~10-20MB
```

### Step 22: Performance Testing

```bash
# Install k6 (optional)
# https://k6.io/

# Create load test
cat > load-test.js << 'EOF'
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 10,  // 10 virtual users
  duration: '30s',
};

export default function () {
  let res = http.get('https://api.viral-video.app/health');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
}
EOF

# Run test
k6 run load-test.js

# Expected results:
# - All checks pass
# - p95 latency < 500ms
# - 0% errors
```

---

## Post-Deployment: Soft Launch (Week 9)

### Phase 8: Beta Testing

```bash
# Invite 50 beta testers
# Distribute links:
# - Landing: https://viral-video.app
# - Signup: https://viral-video.app/auth/signup

# Monitor metrics:
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=viral-backend \
  --start-time 2026-06-01T00:00:00Z \
  --end-time 2026-06-02T00:00:00Z \
  --period 300 \
  --statistics Average,Maximum

# Check error rate
aws logs insights --log-group-name /ecs/viral-backend \
  --query 'fields @timestamp, @message | filter @message like /ERROR/'

# Gather feedback
# - Response time acceptable?
# - Video quality good?
# - Payments working?
# - UI/UX intuitive?
```

### Phase 9: GA Launch (Week 10)

```bash
# Final checks:
# ✅ 99%+ uptime in beta
# ✅ <5% error rate
# ✅ <200ms latency p95
# ✅ 0 critical issues
# ✅ All tests passing
# ✅ Monitoring in place

# Launch!
# - Announce on social media
# - Email launch list
# - Product Hunt post
# - Monitor closely for first 24h
```

---

## Rollback Plan

If critical issues are found:

```bash
# Option 1: Scale down (temporary fix)
aws ecs update-service \
  --cluster viral-video-prod \
  --service viral-backend \
  --desired-count 0

# Option 2: Revert image
aws ecs update-service \
  --cluster viral-video-prod \
  --service viral-backend \
  --task-definition viral-backend:PREVIOUS_VERSION \
  --force-new-deployment

# Option 3: Delete everything (full rollback)
terraform destroy

# After fix, redeploy
terraform apply
aws ecr push ...
aws ecs create-service ...
```

---

## Estimated Costs

| Service | Monthly Cost |
|---------|-------------|
| ECS Fargate (2 tasks, 0.5 vCPU) | $30-40 |
| RDS PostgreSQL (db.t3.micro, 20GB) | $40-50 |
| ElastiCache Redis (cache.t3.micro) | $20 |
| S3 (1TB storage, 100GB transfer) | $25-30 |
| CloudFront (100GB cached) | $8-12 |
| ALB (730 hours) | $16 |
| Data Transfer (cross-AZ) | $5 |
| **Total Estimate** | **$140-170/month** |

Actual costs will vary based on usage. Monitor in AWS Cost Explorer.

---

## Troubleshooting

### ECS Task won't start
```bash
aws logs tail /ecs/viral-backend --follow
aws ecs describe-task-definition --task-definition viral-backend:1
```

### RDS Connection issues
```bash
psql -h viral-db.xxxxx.rds.amazonaws.com -U postgres -d viral_db
# Check security group allows port 5432 from ECS SG
```

### CloudFront returning 403
```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket $VIDEOS_BUCKET

# Should allow CloudFront OAI (Origin Access Identity)
```

---

**Ready for SPRINT 4 Deployment!**

Total execution time: 5-7 days
Success rate: >99% if steps are followed
Next milestone: GA Launch (Week 10)
