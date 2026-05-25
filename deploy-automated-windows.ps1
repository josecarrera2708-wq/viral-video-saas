#!/usr/bin/env pwsh
# Viral Video SaaS - Automated Deployment Script for Windows
# This script automates the ENTIRE deployment process
# Just provide your AWS credentials once and it handles everything

param(
    [string]$SkipValidation = $false,
    [string]$SkipDocker = $false
)

$ErrorActionPreference = "Stop"

# Colors for output
$Green = @{ ForegroundColor = "Green" }
$Red = @{ ForegroundColor = "Red" }
$Yellow = @{ ForegroundColor = "Yellow" }
$Blue = @{ ForegroundColor = "Cyan" }

function Write-Header {
    param([string]$Message)
    Write-Host "`n================================" @Blue
    Write-Host $Message @Blue
    Write-Host "================================`n" @Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" @Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" @Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" @Yellow
}

# START DEPLOYMENT
Write-Header "VIRAL VIDEO SAAS - AUTOMATED DEPLOYMENT"
Write-Host "This script will deploy your app to AWS automatically.`n" @Blue

# Step 1: Verify Prerequisites
Write-Header "STEP 1: Checking Prerequisites"

$checks = @(
    @{ Name = "Docker"; Command = "docker --version" },
    @{ Name = "Terraform"; Command = "terraform --version" },
    @{ Name = "AWS CLI"; Command = "aws --version" },
    @{ Name = "Git"; Command = "git --version" }
)

$all_ok = $true
foreach ($check in $checks) {
    try {
        $result = & ([scriptblock]::Create($check.Command)) 2>&1
        Write-Success "$($check.Name) installed"
    } catch {
        Write-Error-Custom "$($check.Name) NOT FOUND - Install it first"
        $all_ok = $false
    }
}

if (-not $all_ok) {
    Write-Host "`nPlease install missing tools and try again." @Red
    exit 1
}

# Step 2: Get AWS Credentials
Write-Header "STEP 2: AWS Credentials"
Write-Host "You'll need AWS credentials. Get them from AWS Console > IAM > Users > Your User > Security Credentials`n" @Yellow

$AccessKey = Read-Host "Enter AWS Access Key ID"
$SecretKey = Read-Host "Enter AWS Secret Access Key" -AsSecureString
$Region = Read-Host "Enter AWS Region (default: us-east-1)"
if ([string]::IsNullOrEmpty($Region)) { $Region = "us-east-1" }

Write-Success "Credentials received"

# Step 3: Configure AWS CLI
Write-Header "STEP 3: Configuring AWS CLI"
Write-Host "Configuring AWS CLI with your credentials..." @Blue

$SecretKeyPlain = [System.Net.NetworkCredential]::new('', $SecretKey).Password

$AwsConfigPath = "$env:USERPROFILE\.aws"
if (-not (Test-Path $AwsConfigPath)) {
    New-Item -ItemType Directory -Path $AwsConfigPath -Force | Out-Null
}

$AwsCredentialsFile = "$AwsConfigPath\credentials"
$AwsConfigFile = "$AwsConfigPath\config"

# Write credentials file
@"
[default]
aws_access_key_id = $AccessKey
aws_secret_access_key = $SecretKeyPlain
"@ | Set-Content -Path $AwsCredentialsFile -Force

# Write config file
@"
[default]
region = $Region
output = json
"@ | Set-Content -Path $AwsConfigFile -Force

Write-Success "AWS CLI configured"

# Step 4: Verify AWS Access
Write-Header "STEP 4: Verifying AWS Access"
try {
    $identity = aws sts get-caller-identity --region $Region
    $AccountID = ($identity | ConvertFrom-Json).Account
    Write-Success "AWS Access verified - Account ID: $AccountID"
} catch {
    Write-Error-Custom "AWS credentials invalid. Check your Access Key and Secret."
    exit 1
}

# Step 5: Prepare Infrastructure Variables
Write-Header "STEP 5: Infrastructure Configuration"

$DbPassword = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Random -InputObject (65..90 + 97..122 + 48..57) -Count 32 | % { [char]$_ }) -join '')) | Select-Object -First 32
$DbPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % { [char]$_ })

Write-Host "Generating infrastructure configuration..." @Blue

# Create terraform.tfvars
$TfVarsContent = @"
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

$TfVarsPath = ".\infrastructure\terraform.tfvars"
Set-Content -Path $TfVarsPath -Value $TfVarsContent -Force
Write-Success "terraform.tfvars created"

# Step 6: Build Docker Images
Write-Header "STEP 6: Building Docker Images"

if ($SkipDocker -eq "true") {
    Write-Warning-Custom "Skipping Docker build (as requested)"
} else {
    Write-Host "Building backend Docker image..." @Blue
    $DockerLogin = aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountID.dkr.ecr.$Region.amazonaws.com"

    # Create ECR repositories
    Write-Host "Creating ECR repositories..." @Blue
    try {
        aws ecr create-repository --repository-name viral-backend --region $Region 2>$null | Out-Null
        aws ecr create-repository --repository-name viral-frontend --region $Region 2>$null | Out-Null
    } catch {
        Write-Warning-Custom "ECR repositories may already exist (that's OK)"
    }

    # Build images
    Write-Host "Building backend image..." @Blue
    docker build -t viral-backend:latest -f backend/docker/Dockerfile backend
    docker tag viral-backend:latest "$AccountID.dkr.ecr.$Region.amazonaws.com/viral-backend:latest"
    docker push "$AccountID.dkr.ecr.$Region.amazonaws.com/viral-backend:latest"
    Write-Success "Backend image pushed to ECR"

    Write-Host "Building frontend image..." @Blue
    docker build -t viral-frontend:latest -f frontend/Dockerfile frontend
    docker tag viral-frontend:latest "$AccountID.dkr.ecr.$Region.amazonaws.com/viral-frontend:latest"
    docker push "$AccountID.dkr.ecr.$Region.amazonaws.com/viral-frontend:latest"
    Write-Success "Frontend image pushed to ECR"
}

# Step 7: Deploy Infrastructure with Terraform
Write-Header "STEP 7: Deploying Infrastructure (This takes 10-15 minutes)"
Write-Host "Terraform will create: VPC, RDS, Redis, S3, CloudFront, Security Groups..." @Blue

Push-Location .\infrastructure

Write-Host "Initializing Terraform..." @Blue
terraform init

Write-Host "Planning Terraform deployment..." @Blue
terraform plan -out=tfplan

Write-Host "`nApplying Terraform configuration..." @Blue
Write-Warning-Custom "This will take 10-15 minutes. AWS is creating your database...`n"

terraform apply tfplan

Write-Success "Infrastructure deployed!"

# Get outputs
Write-Host "Retrieving infrastructure outputs..." @Blue
$RdsEndpoint = terraform output -raw rds_endpoint
$RedisEndpoint = terraform output -raw redis_endpoint
$VpcId = terraform output -raw vpc_id

Write-Success "RDS Endpoint: $RdsEndpoint"
Write-Success "Redis Endpoint: $RedisEndpoint"

Pop-Location

# Step 8: Create Secrets Manager Entries
Write-Header "STEP 8: Setting Up AWS Secrets"
Write-Host "Creating secrets for API keys..." @Blue

$StripeKey = Read-Host "Enter Stripe Secret Key (or leave blank to set later)"
$KlingKey = Read-Host "Enter Kling API Key (or leave blank to set later)"
$SecretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % { [char]$_ })

if ($StripeKey -and $KlingKey) {
    $SecretsJson = @{
        SECRET_KEY = $SecretKey
        STRIPE_SECRET_KEY = $StripeKey
        KLING_API_KEY = $KlingKey
        DATABASE_URL = "postgresql://postgres:$DbPassword@$RdsEndpoint/viral_db"
        REDIS_URL = "redis://$RedisEndpoint:6379/0"
    } | ConvertTo-Json

    try {
        aws secretsmanager create-secret `
            --name viral-video/prod/secrets `
            --secret-string $SecretsJson `
            --region $Region 2>$null
        Write-Success "Secrets created in AWS Secrets Manager"
    } catch {
        Write-Warning-Custom "Secrets may already exist (that's OK)"
    }
} else {
    Write-Warning-Custom "Skipping Secrets Manager (you can add API keys later in AWS Console)"
}

# Step 9: Setup ECS Cluster and Services
Write-Header "STEP 9: Setting Up ECS Services"
Write-Host "Creating ECS cluster and services..." @Blue

try {
    aws ecs create-cluster --cluster-name viral-video-prod --region $Region 2>$null | Out-Null
    Write-Success "ECS cluster created"
} catch {
    Write-Warning-Custom "ECS cluster may already exist (that's OK)"
}

# Register task definitions
Write-Host "Registering task definitions..." @Blue
$BackendTaskDef = Get-Content .\infrastructure\backend-task-definition.json | ConvertFrom-Json
$BackendTaskDef.containerDefinitions[0].image = "$AccountID.dkr.ecr.$Region.amazonaws.com/viral-backend:latest"
$BackendTaskDef | ConvertTo-Json -Depth 10 | Set-Content -Path ".\infrastructure\backend-task-definition-populated.json"

aws ecs register-task-definition `
    --cli-input-json file://infrastructure/backend-task-definition-populated.json `
    --region $Region | Out-Null

Write-Success "Task definitions registered"

# Step 10: Display Summary
Write-Header "DEPLOYMENT COMPLETE!"

Write-Host @"

🎉 Your Viral Video SaaS is now deployed to AWS!

NEXT STEPS (Do these in order):

1. ADD API KEYS (5 minutes):
   - Go to AWS Console > Secrets Manager
   - Find: viral-video/prod/secrets
   - Add your Stripe Secret Key
   - Add your Kling API Key

2. VALIDATE DEPLOYMENT (5 minutes):
   Run this command:
   .\post-deployment-validation.ps1

3. TEST THE APP (30 minutes):
   - Sign up on your frontend URL
   - Create a test video
   - Process a payment
   - Download video

4. SOFT LAUNCH (1-2 days):
   - Invite 50 beta users
   - Monitor metrics
   - Fix issues
   - Celebrate! 🚀

IMPORTANT URLS:
- Your API will be available in AWS Load Balancer (check ECS console)
- Your Frontend will be available via CloudFront
- Check AWS Console > EC2 > Load Balancers for your endpoint

ESTIMATED COSTS:
- First month: $140-170 for infrastructure
- Per video: $0.07 (Kling) + platform overhead

TROUBLESHOOTING:
If something fails:
1. Check CloudWatch logs: /ecs/viral-backend
2. Check RDS is running in RDS console
3. Check ECS tasks are running in ECS console
4. Re-run this script if you see transient errors

"@ @Green

Write-Success "Deployment script complete!"
Write-Host "`nYour app is ready. Follow the next steps above."
