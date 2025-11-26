#!/bin/bash

###############################################################################
# Frontend Amplify Deployment Script
#
# Builds the Next.js app and uploads artifacts to AWS Amplify.
# Run this script from the repository root directory.
#
# Usage:
#   ./deploy-scripts/frontend-amplify-deploy.sh
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Amplify app already created (via amplify-hosting-stack.ts)
#   - Environment variables set: AMPLIFY_APP_ID, AMPLIFY_BRANCH
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_DIR="Frontend/admissions-chat"
BUILD_DIR=".next"
AMPLIFY_APP_ID="${AMPLIFY_APP_ID:-}"
AMPLIFY_BRANCH="${AMPLIFY_BRANCH:-main}"

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}AI Admissions Agent - Frontend Deployment${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Validate environment variables
if [ -z "$AMPLIFY_APP_ID" ]; then
    echo -e "${RED}Error: AMPLIFY_APP_ID environment variable is not set${NC}"
    echo "Get your App ID from: aws amplify list-apps"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  Amplify App ID: $AMPLIFY_APP_ID"
echo "  Branch: $AMPLIFY_BRANCH"
echo "  Frontend Directory: $FRONTEND_DIR"
echo ""

# Navigate to frontend directory
echo -e "${YELLOW}Step 1: Navigating to frontend directory...${NC}"
cd "$FRONTEND_DIR"

# Install dependencies
echo -e "${YELLOW}Step 2: Installing dependencies...${NC}"
npm ci

# Run type checking
echo -e "${YELLOW}Step 3: Running type check...${NC}"
npm run type-check || {
    echo -e "${RED}Type checking failed. Fix errors before deploying.${NC}"
    exit 1
}

# Run linting
echo -e "${YELLOW}Step 4: Running linter...${NC}"
npm run lint || {
    echo -e "${YELLOW}Warning: Linting issues found. Consider fixing before deploying.${NC}"
}

# Build the Next.js application
echo -e "${YELLOW}Step 5: Building Next.js application...${NC}"
npm run build || {
    echo -e "${RED}Build failed. Check errors above.${NC}"
    exit 1
}

# Verify build output
if [ ! -d "$BUILD_DIR" ]; then
    echo -e "${RED}Error: Build directory $BUILD_DIR not found${NC}"
    exit 1
fi

echo -e "${GREEN}Build completed successfully!${NC}"
echo ""

# Create deployment package
echo -e "${YELLOW}Step 6: Creating deployment package...${NC}"
DEPLOYMENT_PACKAGE="amplify-deployment-$(date +%Y%m%d-%H%M%S).zip"

zip -r "$DEPLOYMENT_PACKAGE" \
    "$BUILD_DIR" \
    "public" \
    "package.json" \
    "next.config.js" \
    ".env.production" 2>/dev/null || true

echo -e "${GREEN}Deployment package created: $DEPLOYMENT_PACKAGE${NC}"
echo ""

# Trigger Amplify deployment
echo -e "${YELLOW}Step 7: Triggering Amplify deployment...${NC}"

# Start deployment
JOB_ID=$(aws amplify start-deployment \
    --app-id "$AMPLIFY_APP_ID" \
    --branch-name "$AMPLIFY_BRANCH" \
    --query 'jobSummary.jobId' \
    --output text)

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}Failed to start Amplify deployment${NC}"
    exit 1
fi

echo -e "${GREEN}Deployment started with Job ID: $JOB_ID${NC}"
echo ""

# Monitor deployment status
echo -e "${YELLOW}Step 8: Monitoring deployment status...${NC}"
echo "Checking deployment progress (this may take a few minutes)..."

MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS=$(aws amplify get-job \
        --app-id "$AMPLIFY_APP_ID" \
        --branch-name "$AMPLIFY_BRANCH" \
        --job-id "$JOB_ID" \
        --query 'job.summary.status' \
        --output text)

    case "$STATUS" in
        "SUCCEED")
            echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
            break
            ;;
        "FAILED"|"CANCELLED")
            echo -e "${RED}✗ Deployment failed with status: $STATUS${NC}"
            echo "Check logs: https://console.aws.amazon.com/amplify/home?region=$(aws configure get region)#/$AMPLIFY_APP_ID/$AMPLIFY_BRANCH/$JOB_ID"
            exit 1
            ;;
        "PENDING"|"RUNNING")
            echo -n "."
            sleep 10
            ;;
        *)
            echo -e "${YELLOW}Unknown status: $STATUS${NC}"
            ;;
    esac

    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${YELLOW}Deployment monitoring timed out. Check Amplify console for status.${NC}"
fi

echo ""

# Get deployment URL
APP_URL=$(aws amplify get-app \
    --app-id "$AMPLIFY_APP_ID" \
    --query "app.defaultDomain" \
    --output text)

BRANCH_URL="https://$AMPLIFY_BRANCH.$APP_URL"

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}================================================${NC}"
echo "  App URL: $BRANCH_URL"
echo "  Console: https://console.aws.amazon.com/amplify/home?region=$(aws configure get region)#/$AMPLIFY_APP_ID"
echo "  Job ID: $JOB_ID"
echo ""
echo -e "${GREEN}Frontend deployed successfully! 🚀${NC}"

# Navigate back to root
cd ../../

# Cleanup
echo -e "${YELLOW}Cleaning up deployment package...${NC}"
rm -f "$FRONTEND_DIR/$DEPLOYMENT_PACKAGE"

echo -e "${GREEN}Done!${NC}"
