#!/bin/bash

# Viral Video SaaS - Pre-Deployment Verification Script
# Checks that everything is ready for AWS deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}DEPLOYMENT READINESS CHECK${NC}"
echo -e "${BLUE}================================${NC}\n"

# Counter for checks
PASSED=0
FAILED=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Check 1: Git repository
echo "1. Checking Git Repository..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    check_pass "Git repository found"
else
    check_fail "Not a git repository"
fi

# Check 2: Required files
echo -e "\n2. Checking Required Files..."
FILES=(
    "backend/requirements.txt"
    "backend/app/main.py"
    "frontend/package.json"
    "infrastructure/main.tf"
    "docker-compose.yml"
    "docs/API.md"
    "SPRINT4_DEPLOYMENT.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_fail "$file missing"
    fi
done

# Check 3: Environment files
echo -e "\n3. Checking Environment Templates..."
if [ -f "backend/.env.example" ]; then
    check_pass "backend/.env.example found"
else
    check_fail "backend/.env.example missing"
fi

if [ -f "infrastructure/terraform.tfvars.example" ]; then
    check_pass "infrastructure/terraform.tfvars.example found"
else
    check_warn "infrastructure/terraform.tfvars.example missing (create from example)"
fi

# Check 4: Dependencies
echo -e "\n3. Checking Installation Dependencies..."

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    check_pass "Docker installed: $DOCKER_VERSION"
else
    check_fail "Docker not installed"
fi

if command -v terraform &> /dev/null; then
    TERRAFORM_VERSION=$(terraform --version | head -1)
    check_pass "Terraform installed"
else
    check_fail "Terraform not installed"
fi

if command -v aws &> /dev/null; then
    check_pass "AWS CLI installed"
else
    check_fail "AWS CLI not installed"
fi

# Check 5: Code quality
echo -e "\n5. Checking Code Structure..."

if [ -d "backend/app" ]; then
    if [ -f "backend/app/main.py" ] && [ -f "backend/app/config.py" ]; then
        check_pass "Backend structure complete"
    else
        check_fail "Backend structure incomplete"
    fi
else
    check_fail "Backend directory not found"
fi

if [ -d "frontend/src" ]; then
    if [ -f "frontend/src/app/page.tsx" ]; then
        check_pass "Frontend structure complete"
    else
        check_fail "Frontend structure incomplete"
    fi
else
    check_fail "Frontend directory not found"
fi

if [ -d "infrastructure" ]; then
    if [ -f "infrastructure/main.tf" ] && [ -f "infrastructure/variables.tf" ]; then
        check_pass "Infrastructure structure complete"
    else
        check_fail "Infrastructure structure incomplete"
    fi
else
    check_fail "Infrastructure directory not found"
fi

# Check 6: Database
echo -e "\n6. Checking Database Setup..."

if grep -q "postgresql" backend/requirements.txt; then
    check_warn "PostgreSQL driver in requirements (update for production RDS)"
fi

if grep -q "sqlalchemy" backend/requirements.txt; then
    check_pass "SQLAlchemy ORM included"
else
    check_fail "SQLAlchemy ORM missing"
fi

# Check 7: Tests
echo -e "\n7. Checking Test Structure..."

if [ -d "backend/app/tests" ]; then
    TEST_FILES=$(find backend/app/tests -name "test_*.py" | wc -l)
    if [ $TEST_FILES -gt 0 ]; then
        check_pass "$TEST_FILES test files found"
    else
        check_fail "No test files found"
    fi
else
    check_fail "Tests directory not found"
fi

# Check 8: Documentation
echo -e "\n8. Checking Documentation..."

DOC_FILES=(
    "README.md"
    "QUICKSTART.md"
    "EXECUTIVE_SUMMARY.md"
    "docs/API.md"
    "docs/SETUP.md"
    "docs/DEPLOYMENT.md"
    "SPRINT4_DEPLOYMENT.md"
)

for doc in "${DOC_FILES[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "$doc found"
    else
        check_fail "$doc missing"
    fi
done

# Check 9: Deployment files
echo -e "\n9. Checking Deployment Files..."

if [ -f "deploy.sh" ]; then
    if [ -x "deploy.sh" ]; then
        check_pass "deploy.sh is executable"
    else
        check_warn "deploy.sh exists but is not executable (run: chmod +x deploy.sh)"
    fi
else
    check_fail "deploy.sh not found"
fi

if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml found"
else
    check_fail "docker-compose.yml missing"
fi

if [ -f "Makefile" ]; then
    check_pass "Makefile found"
else
    check_warn "Makefile not found (useful but optional)"
fi

# Check 10: Git status
echo -e "\n10. Checking Git Status..."

if [ -f ".gitignore" ]; then
    if grep -q ".env" .gitignore; then
        check_pass ".env files in .gitignore"
    else
        check_warn "Ensure .env files are in .gitignore"
    fi

    if grep -q "terraform.tfvars" .gitignore; then
        check_pass "terraform.tfvars in .gitignore"
    else
        check_warn "Ensure terraform.tfvars is in .gitignore"
    fi
else
    check_fail ".gitignore not found"
fi

# Summary
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}SUMMARY${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "✓ Passed: ${GREEN}$PASSED${NC}"
echo -e "✗ Failed: ${RED}$FAILED${NC}"
echo -e "⚠ Warnings: ${YELLOW}$WARNINGS${NC}"
echo -e "${BLUE}================================${NC}\n"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "\nYou are ready to deploy. Next steps:"
    echo "1. Read SPRINT4_DEPLOYMENT.md"
    echo "2. Setup AWS account and credentials"
    echo "3. Run: ./deploy.sh all"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Fix issues above before deploying.${NC}"
    exit 1
fi
