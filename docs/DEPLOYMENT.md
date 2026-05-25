# Deployment Guide - AWS Production

Complete guide to deploy Viral Video SaaS to AWS production environment.

## Prerequisites

- AWS Account with appropriate IAM permissions
- Terraform installed (`brew install terraform`)
- Docker installed and logged into ECR
- Domain name configured (optional, for custom domain)
- Stripe account with API keys
- Kling API keys

## Step 1: Infrastructure Setup with Terraform

```bash
cd infrastructure

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Apply infrastructure
terraform apply

# Save outputs
terraform output > outputs.txt
```

This creates:
- VPC with public/private subnets
- RDS PostgreSQL database
- ElastiCache Redis cluster
- S3 buckets for videos and uploads
- Security groups with proper access rules

## Step 2: Build and Push Docker Images

```bash
# Build images
docker-compose build

# Tag for ECR
docker tag viral-video-saas-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-backend:latest
docker tag viral-video-saas-frontend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-frontend:latest

# Login to ECR (replace account ID)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Push images
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-frontend:latest
```

## Step 3: Create ECS Cluster and Services

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name viral-video-prod

# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs/backend-task-def.json

# Create Fargate service
aws ecs create-service \
  --cluster viral-video-prod \
  --service-name viral-backend \
  --task-definition viral-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## Step 4: Configure Environment Variables

Create `.env.production` with:

```env
# Database
DATABASE_URL=postgresql://postgres:PASSWORD@viral-db.xxx.rds.amazonaws.com:5432/viral_db

# Redis
REDIS_URL=redis://viral-redis.xxx.cache.amazonaws.com:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Kling
KLING_API_KEY=your-key

# AWS
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_VIDEOS=viral-videos-123456789
S3_BUCKET_UPLOADS=viral-uploads-123456789

# Application
SECRET_KEY=your-secure-random-key
DEBUG=False
```

Store securely in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name viral-video/prod \
  --secret-string file://production-secrets.json
```

## Step 5: Setup CloudFront CDN

```bash
# Create CloudFront distribution for S3 videos bucket
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

Configure for:
- Origin: viral-videos-123456789.s3.us-east-1.amazonaws.com
- Cache TTL: 1 day for videos, 5 minutes for API
- HTTPS: Required
- Custom domain: videos.viral-video.app (optional)

## Step 6: Setup RDS Database

```bash
# Connect to RDS
psql -h viral-db.xxx.rds.amazonaws.com -U postgres -d viral_db

# Run migrations (if using Alembic)
alembic upgrade head

# Create initial tables (if not using migrations)
# Tables auto-create from SQLAlchemy models on first run
```

## Step 7: Configure Load Balancer

```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name viral-video-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target groups
aws elbv2 create-target-group \
  --name viral-backend-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx
```

## Step 8: Setup SSL/TLS with ACM

```bash
# Request certificate
aws acm request-certificate \
  --domain-name viral-video.app \
  --subject-alternative-names www.viral-video.app

# Use in ALB listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:...
```

## Step 9: Setup Monitoring and Logging

```bash
# Enable CloudWatch Logs
aws logs create-log-group --log-group-name /ecs/viral-backend

# Setup alarms
aws cloudwatch put-metric-alarm \
  --alarm-name viral-video-error-rate \
  --alarm-description "Alert if error rate > 5%" \
  --metric-name ErrorCount \
  --namespace AWS/ECS \
  --statistic Sum
```

## Step 10: Domain and DNS

```bash
# Point domain to ALB
# In Route53 or your DNS provider:
# - viral-video.app CNAME -> viral-video-alb-123.us-east-1.elb.amazonaws.com
# - api.viral-video.app CNAME -> viral-video-alb-123.us-east-1.elb.amazonaws.com
# - www.viral-video.app CNAME -> viral-video.app
```

## Maintenance

### Database Backups
```bash
# Enable automated backups (done in Terraform)
# Check retention: 7 days
# Manual backup:
aws rds create-db-snapshot \
  --db-instance-identifier viral-db \
  --db-snapshot-identifier viral-db-backup-2026-05-24
```

### Scaling
```bash
# Update desired count (scale up)
aws ecs update-service \
  --cluster viral-video-prod \
  --service viral-backend \
  --desired-count 5
```

### Deploying Updates
```bash
# Build and push new image
docker build -t viral-backend:new-version .
docker tag viral-backend:new-version 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/viral-backend:latest

# Update ECS service (will auto-redeploy)
aws ecs update-service \
  --cluster viral-video-prod \
  --service viral-backend \
  --force-new-deployment
```

### Health Checks
```bash
# Check ECS service status
aws ecs describe-services \
  --cluster viral-video-prod \
  --services viral-backend \
  --query 'services[0].{Status:status,Desired:desiredCount,Running:runningCount}'

# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier viral-db \
  --query 'DBInstances[0].DBInstanceStatus'

# Monitor CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --start-time 2026-05-24T00:00:00Z \
  --end-time 2026-05-25T00:00:00Z \
  --period 300 \
  --statistics Average
```

## Estimated Costs (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| **ECS Fargate** | 2-4 tasks, 0.25-0.5 vCPU, 512MB RAM | $30-50 |
| **RDS PostgreSQL** | db.t3.micro, 20GB storage | $40-50 |
| **ElastiCache Redis** | cache.t3.micro | $20 |
| **S3 Storage** | 500GB videos | $12 |
| **S3 Transfer** | 100GB outbound | $9 |
| **CloudFront** | 100GB cached | $8 |
| **ALB** | 730 hours | $16 |
| **Data Transfer** | Cross-AZ | $5 |
| **Total Estimate** | | **$140-160** |

## Troubleshooting

### ECS Task won't start
```bash
# Check logs
aws logs tail /ecs/viral-backend --follow

# Check task definition
aws ecs describe-task-definition --task-definition viral-backend
```

### Database connection issues
```bash
# Test RDS connection
psql -h viral-db.xxx.rds.amazonaws.com -U postgres -c "SELECT 1;"

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxx
```

### High CPU/Memory usage
```bash
# Scale up
aws ecs update-service --cluster viral-video-prod --service viral-backend --desired-count 4

# Review slow queries
# Connect to RDS and run:
# SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

## Rollback

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

---

**Deployment Status**: Ready for production
**Estimated Deployment Time**: 30-45 minutes
**Last Updated**: May 24, 2026
