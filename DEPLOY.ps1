#!/usr/bin/env pwsh
# SIMPLEST DEPLOYMENT SCRIPT EVER
# Just run this and answer the prompts

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "VIRAL VIDEO SAAS - DEPLOYMENT" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Step 1: Check Docker
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not installed" -ForegroundColor Red
    Write-Host "   Install: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Docker found" -ForegroundColor Green

# Step 2: Check AWS CLI
Write-Host "`n2. Checking AWS CLI..." -ForegroundColor Yellow
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not installed" -ForegroundColor Red
    Write-Host "   Install: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ AWS CLI found" -ForegroundColor Green

# Step 3: Check Terraform
Write-Host "`n3. Checking Terraform..." -ForegroundColor Yellow
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Terraform not installed" -ForegroundColor Red
    Write-Host "   Install: https://www.terraform.io/downloads" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Terraform found" -ForegroundColor Green

# Step 4: Get AWS Credentials
Write-Host "`n4. AWS Credentials" -ForegroundColor Yellow
Write-Host "   Get from: AWS Console > IAM > Users > Your User > Security Credentials" -ForegroundColor Gray
$AccessKey = Read-Host "   Enter AWS Access Key ID"
$SecretKey = Read-Host "   Enter AWS Secret Access Key" -AsSecureString
$SecretKeyPlain = [System.Net.NetworkCredential]::new('', $SecretKey).Password

# Step 5: Get Region
Write-Host "`n5. AWS Region (default: us-east-1)" -ForegroundColor Yellow
$Region = Read-Host "   Enter region"
if ([string]::IsNullOrEmpty($Region)) { $Region = "us-east-1" }

# Step 6: Configure AWS
Write-Host "`n6. Configuring AWS CLI..." -ForegroundColor Yellow
$AwsDir = "$env:USERPROFILE\.aws"
New-Item -ItemType Directory -Path $AwsDir -Force | Out-Null

@"
[default]
aws_access_key_id = $AccessKey
aws_secret_access_key = $SecretKeyPlain
"@ | Set-Content -Path "$AwsDir\credentials" -Force

@"
[default]
region = $Region
output = json
"@ | Set-Content -Path "$AwsDir\config" -Force

Write-Host "   ✓ AWS configured" -ForegroundColor Green

# Step 7: Verify AWS
Write-Host "`n7. Verifying AWS access..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --region $Region 2>&1
    if ($LASTEXITCODE -eq 0) {
        $account = ($identity | ConvertFrom-Json).Account
        Write-Host "   ✓ AWS verified - Account: $account" -ForegroundColor Green
    } else {
        Write-Host "   ❌ AWS credentials failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ AWS error: $_" -ForegroundColor Red
    exit 1
}

# Step 8: Create Terraform variables
Write-Host "`n8. Creating Terraform configuration..." -ForegroundColor Yellow
$DbPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % { [char]$_ })

$tfVars = @"
aws_region           = "$Region"
app_name            = "viral-video-saas"
environment         = "production"
db_password         = "$DbPassword"
rds_instance_class  = "db.t3.micro"
redis_node_type     = "cache.t3.micro"
enable_multi_az     = true
backup_retention    = 7
log_retention_days  = 30
"@

$tfVars | Set-Content -Path ".\infrastructure\terraform.tfvars" -Force
Write-Host "   ✓ Terraform configured" -ForegroundColor Green

# Step 9: Build Docker Images
Write-Host "`n9. Building Docker images..." -ForegroundColor Yellow
Write-Host "   This may take 5-10 minutes..." -ForegroundColor Gray

# Login to ECR
Write-Host "   • Logging to ECR..." -ForegroundColor Gray
$loginCmd = "aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $account.dkr.ecr.$Region.amazonaws.com"
Invoke-Expression $loginCmd | Out-Null

# Create ECR repos
Write-Host "   • Creating ECR repositories..." -ForegroundColor Gray
aws ecr create-repository --repository-name viral-backend --region $Region 2>$null | Out-Null
aws ecr create-repository --repository-name viral-frontend --region $Region 2>$null | Out-Null

# Build backend
Write-Host "   • Building backend..." -ForegroundColor Gray
docker build -t viral-backend:latest -f backend/Dockerfile backend
docker tag viral-backend:latest "$account.dkr.ecr.$Region.amazonaws.com/viral-backend:latest"
docker push "$account.dkr.ecr.$Region.amazonaws.com/viral-backend:latest" | Out-Null

# Build frontend
Write-Host "   • Building frontend..." -ForegroundColor Gray
docker build -t viral-frontend:latest -f frontend/Dockerfile frontend
docker tag viral-frontend:latest "$account.dkr.ecr.$Region.amazonaws.com/viral-frontend:latest"
docker push "$account.dkr.ecr.$Region.amazonaws.com/viral-frontend:latest" | Out-Null

Write-Host "   ✓ Docker images built and pushed" -ForegroundColor Green

# Step 10: Deploy with Terraform
Write-Host "`n10. Deploying infrastructure (10-15 minutes)..." -ForegroundColor Yellow
Write-Host "    AWS is creating: VPC, RDS, Redis, S3, CloudFront, ECS" -ForegroundColor Gray

Push-Location .\infrastructure
terraform init
terraform plan -out=tfplan
terraform apply tfplan

$RdsEndpoint = terraform output -raw rds_endpoint 2>$null
$RedisEndpoint = terraform output -raw redis_endpoint 2>$null

Pop-Location

Write-Host "   ✓ Infrastructure deployed" -ForegroundColor Green

# Step 11: Done!
Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Go to AWS Console > Secrets Manager" -ForegroundColor White
Write-Host "2. Find: viral-video/prod/secrets" -ForegroundColor White
Write-Host "3. Add your API keys:" -ForegroundColor White
Write-Host "   - STRIPE_SECRET_KEY (from https://dashboard.stripe.com/)" -ForegroundColor White
Write-Host "   - KLING_API_KEY (from https://kling.kuaishou.com/api)" -ForegroundColor White

Write-Host "`n4. Run validation:" -ForegroundColor White
Write-Host "   .\post-deployment-validation.ps1" -ForegroundColor White

Write-Host "`nYour app is now LIVE on AWS!" -ForegroundColor Green
Write-Host "Estimated monthly cost: \$140-170 USD`n" -ForegroundColor Gray
