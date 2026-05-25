#!/bin/bash

# Viral Video SaaS - Automated Deployment Script
# This script automates the AWS deployment process
# Usage: ./deploy.sh [init|plan|apply|destroy]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TERRAFORM_DIR="$SCRIPT_DIR/infrastructure"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Install it from: https://aws.amazon.com/cli/"
        exit 1
    fi

    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Install it from: https://www.terraform.io/downloads.html"
        exit 1
    fi

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Install it from: https://www.docker.com/"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi

    log_info "All prerequisites met!"
}

build_docker_images() {
    log_info "Building Docker images..."

    cd "$SCRIPT_DIR"

    # Backend image
    log_info "Building backend image..."
    docker build -t viral-backend:latest -f "$BACKEND_DIR/docker/Dockerfile" "$BACKEND_DIR/"

    # Frontend image
    log_info "Building frontend image..."
    if [ -f "$FRONTEND_DIR/Dockerfile" ]; then
        docker build -t viral-frontend:latest -f "$FRONTEND_DIR/Dockerfile" "$FRONTEND_DIR/"
    else
        log_warn "Frontend Dockerfile not found, skipping frontend build"
    fi

    log_info "Docker images built successfully!"
}

push_to_ecr() {
    log_info "Pushing images to ECR..."

    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=${AWS_REGION:-us-east-1}

    BACKEND_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/viral-backend"
    FRONTEND_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/viral-frontend"

    # Create ECR repositories if they don't exist
    log_info "Creating ECR repositories..."
    aws ecr create-repository --repository-name viral-backend --region $AWS_REGION 2>/dev/null || true
    aws ecr create-repository --repository-name viral-frontend --region $AWS_REGION 2>/dev/null || true

    # Login to ECR
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

    # Tag and push backend
    log_info "Pushing backend image..."
    docker tag viral-backend:latest "$BACKEND_URI:latest"
    docker push "$BACKEND_URI:latest"

    # Tag and push frontend
    log_info "Pushing frontend image..."
    docker tag viral-frontend:latest "$FRONTEND_URI:latest"
    docker push "$FRONTEND_URI:latest"

    log_info "Images pushed to ECR successfully!"

    # Save URIs for later
    echo "$BACKEND_URI" > /tmp/backend-uri.txt
    echo "$FRONTEND_URI" > /tmp/frontend-uri.txt
}

terraform_init() {
    log_info "Initializing Terraform..."
    cd "$TERRAFORM_DIR"
    terraform init
    log_info "Terraform initialized!"
}

terraform_plan() {
    log_info "Running Terraform plan..."
    cd "$TERRAFORM_DIR"

    # Check if terraform.tfvars exists
    if [ ! -f "terraform.tfvars" ]; then
        log_error "terraform.tfvars not found!"
        log_info "Create it with: cp terraform.tfvars.example terraform.tfvars"
        log_info "Then edit it with your AWS settings"
        exit 1
    fi

    terraform plan -out=tfplan
    log_info "Plan saved to tfplan"
}

terraform_apply() {
    log_info "Applying Terraform configuration..."
    cd "$TERRAFORM_DIR"

    if [ ! -f "tfplan" ]; then
        log_error "tfplan not found! Run 'deploy.sh plan' first"
        exit 1
    fi

    log_warn "This will create AWS resources and incur costs!"
    read -p "Continue with deployment? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi

    terraform apply tfplan

    # Save outputs
    log_info "Saving deployment outputs..."
    terraform output > deployment-outputs.txt

    log_info "Infrastructure deployed successfully!"
    log_info "Outputs saved to: $TERRAFORM_DIR/deployment-outputs.txt"
}

terraform_destroy() {
    log_warn "This will DESTROY all AWS resources!"
    read -p "Type 'destroy' to confirm: " -r

    if [ "$REPLY" != "destroy" ]; then
        log_info "Destruction cancelled"
        exit 0
    fi

    cd "$TERRAFORM_DIR"
    terraform destroy
    log_info "Resources destroyed"
}

deploy_to_ecs() {
    log_info "Deploying to ECS..."

    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=${AWS_REGION:-us-east-1}

    # Create ECS cluster
    log_info "Creating ECS cluster..."
    aws ecs create-cluster --cluster-name viral-video-prod --region $AWS_REGION 2>/dev/null || true

    # Create task definitions (requires task definition JSON files)
    # This is a placeholder - actual task definitions need to be created
    log_info "Task definitions need to be registered manually or via CloudFormation"
    log_info "See SPRINT4_DEPLOYMENT.md for detailed instructions"
}

print_usage() {
    cat << EOF
Usage: ./deploy.sh [command]

Commands:
    check           Check prerequisites
    build           Build Docker images
    push            Push images to ECR
    init            Initialize Terraform
    plan            Plan infrastructure changes
    apply           Apply infrastructure changes
    destroy         Destroy all infrastructure
    all             Run: check, build, push, init, plan, apply
    help            Show this help message

Environment Variables:
    AWS_REGION      AWS region (default: us-east-1)

Examples:
    ./deploy.sh check           # Verify setup
    ./deploy.sh build           # Build Docker images
    ./deploy.sh push            # Push to ECR
    ./deploy.sh init            # Initialize Terraform
    ./deploy.sh plan            # Plan deployment
    ./deploy.sh apply           # Deploy to AWS
    ./deploy.sh all             # Full deployment

For full deployment guide, see: SPRINT4_DEPLOYMENT.md
EOF
}

# Main script
case "${1:-help}" in
    check)
        check_prerequisites
        ;;
    build)
        build_docker_images
        ;;
    push)
        push_to_ecr
        ;;
    init)
        check_prerequisites
        terraform_init
        ;;
    plan)
        check_prerequisites
        terraform_plan
        ;;
    apply)
        check_prerequisites
        terraform_apply
        ;;
    destroy)
        check_prerequisites
        terraform_destroy
        ;;
    all)
        check_prerequisites
        build_docker_images
        push_to_ecr
        terraform_init
        terraform_plan
        terraform_apply
        ;;
    help)
        print_usage
        ;;
    *)
        log_error "Unknown command: $1"
        print_usage
        exit 1
        ;;
esac

log_info "Done!"
