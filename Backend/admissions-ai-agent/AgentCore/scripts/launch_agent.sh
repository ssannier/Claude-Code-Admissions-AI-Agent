#!/bin/bash

###############################################################################
# Bedrock AgentCore Launch Script
#
# Builds and deploys the Nemo agent to Amazon Bedrock AgentCore.
# This script should be run after the agent has been configured using
# `agentcore configure`.
#
# Usage:
#   cd Backend/admissions-ai-agent/AgentCore
#   ./scripts/launch_agent.sh
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Docker installed and running
#   - Strands CLI installed: pip install strands-sdk
#   - Agent configured: agentcore configure
#   - ECR repository created (from CDK stack)
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_NAME="Nemo"
AGENT_DIR="$(pwd)"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-admissions-agent}"

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Bedrock AgentCore - Agent Launch${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not found. Please install it first.${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon not running. Please start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found and running${NC}"

# Check Strands CLI
if ! command -v agentcore &> /dev/null; then
    echo -e "${RED}Error: Strands CLI (agentcore) not found.${NC}"
    echo "Install it with: pip install strands-sdk"
    exit 1
fi
echo -e "${GREEN}✓ Strands CLI found${NC}"

# Check if agent is configured
if [ ! -f ".agentcore/config.json" ]; then
    echo -e "${RED}Error: Agent not configured.${NC}"
    echo "Run 'agentcore configure' first to set up:"
    echo "  - Execution role ARN"
    echo "  - ECR repository URI"
    echo "  - Bedrock Memory ID"
    exit 1
fi
echo -e "${GREEN}✓ Agent configuration found${NC}"
echo ""

# Display configuration
echo -e "${YELLOW}Configuration:${NC}"
echo "  Agent Name: $AGENT_NAME"
echo "  AWS Region: $AWS_REGION"
echo "  ECR Repository: $ECR_REPOSITORY"
echo "  Working Directory: $AGENT_DIR"
echo ""

# Verify required files
echo -e "${YELLOW}Verifying agent files...${NC}"
REQUIRED_FILES=("agent.py" "Dockerfile" "requirements.txt" "tools/")

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -e "$file" ]; then
        echo -e "${RED}Error: Required file/directory not found: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ $file${NC}"
done
echo ""

# Get AWS account ID
echo -e "${YELLOW}Getting AWS account information...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: Unable to get AWS account ID. Check AWS credentials.${NC}"
    exit 1
fi
echo -e "${GREEN}AWS Account ID: $AWS_ACCOUNT_ID${NC}"
echo ""

# Construct ECR URI
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"
echo -e "${YELLOW}ECR Repository URI: $ECR_URI${NC}"
echo ""

# Login to ECR
echo -e "${YELLOW}Logging in to Amazon ECR...${NC}"
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$ECR_URI" || {
    echo -e "${RED}Failed to login to ECR${NC}"
    exit 1
}
echo -e "${GREEN}✓ Successfully logged in to ECR${NC}"
echo ""

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$ECR_URI:$IMAGE_TAG"

docker build -t "$AGENT_NAME:$IMAGE_TAG" . || {
    echo -e "${RED}Docker build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo ""

# Tag image for ECR
echo -e "${YELLOW}Tagging image for ECR...${NC}"
docker tag "$AGENT_NAME:$IMAGE_TAG" "$FULL_IMAGE_NAME"
echo -e "${GREEN}✓ Image tagged: $FULL_IMAGE_NAME${NC}"
echo ""

# Push image to ECR
echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push "$FULL_IMAGE_NAME" || {
    echo -e "${RED}Failed to push image to ECR${NC}"
    exit 1
}
echo -e "${GREEN}✓ Image pushed to ECR successfully${NC}"
echo ""

# Launch agent with Strands CLI
echo -e "${YELLOW}Deploying agent to Bedrock AgentCore...${NC}"
echo "This may take several minutes..."
echo ""

agentcore launch --image-uri "$FULL_IMAGE_NAME" || {
    echo -e "${RED}Agent launch failed${NC}"
    echo "Check the error messages above for details"
    exit 1
}

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Agent Deployed Successfully! 🚀${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Get agent information
if [ -f ".agentcore/agent.json" ]; then
    AGENT_ID=$(jq -r '.agentId' .agentcore/agent.json 2>/dev/null || echo "")
    AGENT_ARN=$(jq -r '.agentArn' .agentcore/agent.json 2>/dev/null || echo "")

    if [ -n "$AGENT_ID" ]; then
        echo -e "${BLUE}Agent Details:${NC}"
        echo "  Agent ID: $AGENT_ID"
        echo "  Agent ARN: $AGENT_ARN"
        echo "  Image URI: $FULL_IMAGE_NAME"
        echo ""
        echo -e "${YELLOW}Next Steps:${NC}"
        echo "  1. Update your Agent Proxy Lambda environment variables:"
        echo "     AGENT_ID=$AGENT_ID"
        echo "     AGENT_ALIAS_ID=<get from Bedrock console>"
        echo ""
        echo "  2. Test your agent:"
        echo "     agentcore test --agent-id $AGENT_ID"
        echo ""
        echo "  3. Monitor your agent in the AWS Console:"
        echo "     https://console.aws.amazon.com/bedrock/home?region=$AWS_REGION#/agents/$AGENT_ID"
        echo ""
    fi
fi

echo -e "${GREEN}Deployment complete!${NC}"

# Cleanup local Docker images
echo -e "${YELLOW}Cleaning up local Docker images...${NC}"
docker rmi "$AGENT_NAME:$IMAGE_TAG" 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

exit 0
