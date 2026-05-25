# Manual AWS Deployment - Step by Step

If you prefer to deploy manually instead of using `./deploy.sh`, follow these steps.

**Estimated Time**: 2-3 hours
**Prerequisites**: AWS Account, Docker installed, Terraform installed, AWS CLI configured

---

## Step 1: Prepare AWS Environment (15 minutes)

### 1.1 Get AWS Account ID
```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo $AWS_ACCOUNT_ID
# Save this value, you'll need it frequently
```

### 1.2 Set Environment Variables
```bash
export AWS_ACCOUNT_ID=123456789012  # Replace with your account ID
export AWS_REGION=us-east-1
export BACKEND_REPO_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/viral-backend
export FRONTEND_REPO_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/viral-frontend
```

### 1.3 Create ECR Repositories
```bash
# Backend repository
aws ecr create-repository \
  --repository-name viral-backend \
  --region $AWS_REGION

# Frontend repository
aws ecr create-repository \
  --repository-name viral-frontend \
  --region $AWS_REGION

# Output should show URIs - save them
```

---

## Step 2: Build & Push Docker Images (20 minutes)

### 2.1 Login to ECR
```bash
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

### 2.2 Build Backend Image
```bash
cd backend
docker build -t viral-backend:latest .
cd ..
```

### 2.3 Build Frontend Image
```bash
cd frontend
# Assuming Dockerfile exists
docker build -t viral-frontend:latest .
cd ..
```

### 2.4 Tag Images
```bash
docker tag viral-backend:latest $BACKEND_REPO_URI:latest
docker tag viral-frontend:latest $FRONTEND_REPO_URI:latest
```

### 2.5 Push to ECR
```bash
docker push $BACKEND_REPO_URI:latest
docker push $FRONTEND_REPO_URI:latest

# Verify
aws ecr list-images --repository-name viral-backend
aws ecr list-images --repository-name viral-frontend
```

---

## Step 3: Configure Terraform (15 minutes)

### 3.1 Create terraform.tfvars
```bash
cd infrastructure

# Copy and edit template
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
cat > terraform.tfvars << EOF
aws_region           = "us-east-1"
app_name            = "viral-video-saas"
environment         = "production"
db_password         = "$(openssl rand -base64 32)"
rds_instance_class  = "db.t3.micro"
redis_node_type     = "cache.t3.micro"
enable_multi_az     = true
backup_retention    = 7
log_retention_days  = 30
EOF
```

### 3.2 Initialize Terraform
```bash
terraform init
```

### 3.3 Review Plan
```bash
terraform plan -out=tfplan

# Review output - should show ~50 resources to create
```

---

## Step 4: Deploy Infrastructure (30 minutes)

### 4.1 Apply Terraform Configuration
```bash
# This will take 10-15 minutes
terraform apply tfplan

# Monitor in AWS Console:
# - VPC creation
# - RDS instance startup
# - Redis cluster creation
# - S3 buckets
```

### 4.2 Get Outputs
```bash
# Save outputs for next steps
terraform output -raw rds_endpoint > ../rds-endpoint.txt
terraform output -raw redis_endpoint > ../redis-endpoint.txt
terraform output -raw s3_videos_bucket > ../s3-videos.txt
terraform output -raw s3_uploads_bucket > ../s3-uploads.txt

# Display all outputs
terraform output
```

---

## Step 5: Setup Secrets in AWS (10 minutes)

### 5.1 Create RDS Secret
```bash
RDS_ENDPOINT=$(cat ../rds-endpoint.txt)

aws secretsmanager create-secret \
  --name viral-video/prod/database \
  --secret-string "postgresql://postgres:PASSWORD@$RDS_ENDPOINT:5432/viral_db" \
  --region $AWS_REGION
```

### 5.2 Create Redis Secret
```bash
REDIS_ENDPOINT=$(cat ../redis-endpoint.txt)

aws secretsmanager create-secret \
  --name viral-video/prod/redis \
  --secret-string "redis://$REDIS_ENDPOINT:6379/0" \
  --region $AWS_REGION
```

### 5.3 Create App Secrets
```bash
aws secretsmanager create-secret \
  --name viral-video/prod/secrets \
  --secret-string '{
    "SECRET_KEY": "'$(openssl rand -hex 32)'",
    "STRIPE_SECRET_KEY": "sk_live_YOUR_STRIPE_KEY",
    "KLING_API_KEY": "YOUR_KLING_KEY",
    "ELEVENLABS_API_KEY": "optional"
  }' \
  --region $AWS_REGION
```

---

## Step 6: Create ECS Cluster (5 minutes)

### 6.1 Create Cluster
```bash
aws ecs create-cluster \
  --cluster-name viral-video-prod \
  --region $AWS_REGION
```

### 6.2 Update Task Definition
Update `backend-task-definition.json`:
- Replace `BACKEND_IMAGE_URI` with your actual URI: `$BACKEND_REPO_URI:latest`
- Replace `ACCOUNT_ID` with your AWS account ID

```bash
# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://backend-task-definition.json \
  --region $AWS_REGION
```

---

## Step 7: Create Services (10 minutes)

### 7.1 Get VPC/Subnet IDs from Terraform
```bash
terraform output vpc_id
terraform output public_subnet_id
terraform output rds_security_group_id
```

### 7.2 Create Backend Service
```bash
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
  --region $AWS_REGION
```

---

## Step 8: Setup Database (10 minutes)

### 8.1 Connect to RDS
```bash
RDS_ENDPOINT=$(cat ../rds-endpoint.txt)

psql -h $RDS_ENDPOINT -U postgres -d viral_db << EOF
-- Create extensions
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- Create indexes
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_state ON videos(state);
CREATE INDEX idx_credit_transactions_user_id ON credit_transactions(user_id);

-- Verify tables
\dt
EOF
```

---

## Step 9: Setup CloudFront CDN (5 minutes)

### 9.1 Create Distribution
```bash
# Get S3 bucket domain
S3_BUCKET=$(cat ../s3-videos.txt)
S3_DOMAIN="$S3_BUCKET.s3.amazonaws.com"

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name $S3_DOMAIN \
  --default-root-object index.html \
  --region $AWS_REGION
```

---

## Step 10: Configure DNS (5 minutes)

### 10.1 Get ALB DNS Name
```bash
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[0].DNSName' \
  --region $AWS_REGION \
  --output text)

echo "ALB DNS: $ALB_DNS"
```

### 10.2 Update Route53
```bash
# If domain is in Route53
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123XYZABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.viral-video.app",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$ALB_DNS'"}]
      }
    }]
  }'
```

Or if domain is elsewhere:
1. Log into domain registrar
2. Create CNAME: `api.viral-video.app` → ALB DNS name
3. Create CNAME: `www.viral-video.app` → `api.viral-video.app`
4. Create CNAME: `videos.viral-video.app` → CloudFront domain

---

## Step 11: Setup SSL/TLS (10 minutes)

### 11.1 Request Certificate in ACM
```bash
aws acm request-certificate \
  --domain-name viral-video.app \
  --subject-alternative-names www.viral-video.app api.viral-video.app \
  --validation-method DNS \
  --region us-east-1
```

### 11.2 Verify Certificate
- Check email for verification link
- Or verify DNS records in Route53
- Takes 5-30 minutes to validate

---

## Step 12: Configure Load Balancer (10 minutes)

### 12.1 Create Target Group
```bash
aws elbv2 create-target-group \
  --name viral-backend-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --region $AWS_REGION
```

### 12.2 Create ALB (if not created by Terraform)
```bash
aws elbv2 create-load-balancer \
  --name viral-video-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application \
  --region $AWS_REGION
```

---

## Step 13: Setup Monitoring (15 minutes)

### 13.1 Create CloudWatch Log Groups
```bash
aws logs create-log-group --log-group-name /ecs/viral-backend
aws logs create-log-group --log-group-name /ecs/viral-frontend
aws logs create-log-group --log-group-name /rds/viral-db
```

### 13.2 Create Alarms
```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name viral-backend-high-cpu \
  --alarm-description "Alert if CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:your-topic

# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name viral-backend-errors \
  --alarm-description "Alert if error rate > 5%" \
  --metric-name 4XXError \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold
```

---

## Step 14: Verify Deployment (15 minutes)

### 14.1 Run Validation Script
```bash
cd ..
chmod +x post-deployment-validation.sh
./post-deployment-validation.sh
```

### 14.2 Manual Testing
```bash
# Test health check
curl -I https://api.viral-video.app/health

# Test API docs
curl -I https://api.viral-video.app/docs

# Test frontend
curl -I https://viral-video.app

# Test signup endpoint
curl -X POST https://api.viral-video.app/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"test123",
    "name":"Test User"
  }'
```

---

## Troubleshooting

### ECS Task Won't Start
```bash
# Check logs
aws logs tail /ecs/viral-backend --follow

# Check task definition
aws ecs describe-task-definition --task-definition viral-backend:1
```

### RDS Connection Failed
```bash
# Verify security group allows 5432
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Test connection
psql -h $RDS_ENDPOINT -U postgres -d viral_db -c "SELECT 1;"
```

### CloudFront Returns 403
```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket viral-videos-xxxxx

# Verify CloudFront Origin Access Identity (OAI)
aws cloudfront list-distributions
```

---

## After Successful Deployment

1. ✅ Monitor CloudWatch for errors
2. ✅ Test the signup/login flow
3. ✅ Test video creation (if Kling API key is set)
4. ✅ Test payment flow (use Stripe test card)
5. ✅ Soft launch to 50 beta users
6. ✅ GA Launch!

---

## Next Steps

- See [SPRINT4_DEPLOYMENT.md](./SPRINT4_DEPLOYMENT.md) for full context
- See [docs/PRODUCTION_CHECKLIST.md](./docs/PRODUCTION_CHECKLIST.md) for pre-launch validation
- See [post-deployment-validation.sh](./post-deployment-validation.sh) for automated testing

**Estimated Total Time**: 2-3 hours from start to ready for beta testing
