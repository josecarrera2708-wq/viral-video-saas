#!/bin/bash

# Viral Video SaaS - Post-Deployment Validation Script
# Run this after AWS deployment to verify everything is working

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}POST-DEPLOYMENT VALIDATION${NC}"
echo -e "${BLUE}================================${NC}\n"

PASSED=0
FAILED=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

# Get URLs from user
read -p "Enter Backend API URL (e.g., https://api.viral-video.app): " API_URL
read -p "Enter Frontend URL (e.g., https://viral-video.app): " FRONTEND_URL

# Validate URLs
if [ -z "$API_URL" ] || [ -z "$FRONTEND_URL" ]; then
    echo -e "${RED}Error: URLs cannot be empty${NC}"
    exit 1
fi

# Remove trailing slashes
API_URL="${API_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"

echo -e "\nValidating API URL: $API_URL"
echo -e "Validating Frontend URL: $FRONTEND_URL\n"

# Test 1: API Health Check
echo "1. Testing API Health..."
if HEALTH=$(curl -s -w "\n%{http_code}" "$API_URL/health"); then
    HTTP_CODE=$(echo "$HEALTH" | tail -n1)
    if [ "$HTTP_CODE" = "200" ]; then
        check_pass "API health check passed (HTTP 200)"
    else
        check_fail "API health check failed (HTTP $HTTP_CODE)"
    fi
else
    check_fail "API health check failed (connection error)"
fi

# Test 2: API Docs
echo -e "\n2. Testing API Documentation..."
if DOCS=$(curl -s -w "\n%{http_code}" "$API_URL/docs"); then
    HTTP_CODE=$(echo "$DOCS" | tail -n1)
    if [ "$HTTP_CODE" = "200" ]; then
        check_pass "API docs available (HTTP 200)"
    else
        check_fail "API docs not available (HTTP $HTTP_CODE)"
    fi
else
    check_fail "API docs request failed"
fi

# Test 3: Frontend Load
echo -e "\n3. Testing Frontend..."
if FRONTEND=$(curl -s -w "\n%{http_code}" "$FRONTEND_URL"); then
    HTTP_CODE=$(echo "$FRONTEND" | tail -n1)
    if [ "$HTTP_CODE" = "200" ]; then
        check_pass "Frontend loads successfully (HTTP 200)"
    else
        check_fail "Frontend failed to load (HTTP $HTTP_CODE)"
    fi
else
    check_fail "Frontend request failed"
fi

# Test 4: HTTPS
echo -e "\n4. Checking HTTPS..."
if [[ "$API_URL" == https* ]]; then
    check_pass "API uses HTTPS"
else
    check_fail "API does not use HTTPS"
fi

if [[ "$FRONTEND_URL" == https* ]]; then
    check_pass "Frontend uses HTTPS"
else
    check_fail "Frontend does not use HTTPS"
fi

# Test 5: CORS
echo -e "\n5. Checking CORS Headers..."
CORS=$(curl -s -i -X OPTIONS "$API_URL/health" 2>/dev/null | grep -i "access-control-allow")
if [ ! -z "$CORS" ]; then
    check_pass "CORS headers present"
else
    check_fail "CORS headers missing"
fi

# Test 6: Response Time
echo -e "\n6. Checking Response Time..."
START=$(date +%s%N)
curl -s "$API_URL/health" > /dev/null
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))  # Convert to milliseconds

if [ $ELAPSED -lt 500 ]; then
    check_pass "API response time: ${ELAPSED}ms (excellent)"
elif [ $ELAPSED -lt 1000 ]; then
    check_pass "API response time: ${ELAPSED}ms (good)"
else
    check_fail "API response time: ${ELAPSED}ms (slow)"
fi

# Test 7: Database Connection
echo -e "\n7. Checking Database..."
read -p "Enter RDS Endpoint (e.g., viral-db.xxxxx.rds.amazonaws.com): " RDS_ENDPOINT
read -s -p "Enter RDS Master Username: " RDS_USER
echo ""
read -s -p "Enter RDS Master Password: " RDS_PASS
echo ""

if command -v psql &> /dev/null; then
    if PGPASSWORD="$RDS_PASS" psql -h "$RDS_ENDPOINT" -U "$RDS_USER" -d viral_db -c "SELECT 1;" > /dev/null 2>&1; then
        check_pass "Database connection successful"
    else
        check_fail "Database connection failed"
    fi
else
    echo -e "${YELLOW}⚠${NC} psql not installed (install postgresql client to test database)"
fi

# Test 8: S3 Buckets
echo -e "\n8. Checking S3 Buckets..."
if command -v aws &> /dev/null; then
    if aws s3 ls > /dev/null 2>&1; then
        BUCKETS=$(aws s3 ls | grep viral | wc -l)
        if [ $BUCKETS -gt 0 ]; then
            check_pass "S3 buckets found ($BUCKETS)"
        else
            check_fail "No S3 buckets found"
        fi
    else
        check_fail "AWS CLI access failed"
    fi
else
    echo -e "${YELLOW}⚠${NC} AWS CLI not installed"
fi

# Test 9: CloudWatch Logs
echo -e "\n9. Checking CloudWatch Logs..."
if command -v aws &> /dev/null; then
    if aws logs describe-log-groups --log-group-name-prefix /ecs/viral > /dev/null 2>&1; then
        check_pass "CloudWatch logs found"
    else
        check_fail "CloudWatch logs not accessible"
    fi
fi

# Test 10: SSL Certificate
echo -e "\n10. Checking SSL Certificate..."
if command -v openssl &> /dev/null; then
    DOMAIN=$(echo "$API_URL" | sed 's/https:\/\///' | cut -d'/' -f1)
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" < /dev/null 2>/dev/null | openssl x509 -noout -dates > /dev/null 2>&1; then
        EXPIRY=$(openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" < /dev/null 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
        check_pass "SSL certificate valid (expires: $EXPIRY)"
    else
        check_fail "SSL certificate check failed"
    fi
fi

# Summary
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}VALIDATION SUMMARY${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "✓ Passed: ${GREEN}$PASSED${NC}"
echo -e "✗ Failed: ${RED}$FAILED${NC}"
echo -e "${BLUE}================================${NC}\n"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validation checks passed!${NC}"
    echo -e "\nYour deployment is successful. Next steps:"
    echo "1. Monitor CloudWatch for errors"
    echo "2. Test signup/login flow"
    echo "3. Test video creation (requires Kling API key)"
    echo "4. Test payment flow (use Stripe test card)"
    echo "5. Soft launch to 50 beta users"
    exit 0
else
    echo -e "${RED}✗ Some validation checks failed.${NC}"
    echo -e "\nFailed checks need attention before soft launch."
    exit 1
fi
