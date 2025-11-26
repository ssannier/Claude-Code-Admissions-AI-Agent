#!/bin/bash

###############################################################################
# Quick Start Script for Local Testing
#
# This script sets up and runs all components needed for local testing:
# 1. Mock backend servers (Form API + Agent Proxy)
# 2. Frontend development server
#
# Usage: ./start-local-testing.sh
###############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}AI Admissions Agent - Local Testing Setup${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js not found. Please install Node.js first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"

if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm not found. Please install npm first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm found: $(npm --version)${NC}"

echo ""

# Step 1: Install mock server dependencies
echo -e "${YELLOW}Step 1: Installing mock server dependencies...${NC}"
cd mock-servers
if [ ! -d "node_modules" ]; then
    npm install
else
    echo -e "${BLUE}Dependencies already installed${NC}"
fi
cd ..
echo -e "${GREEN}✓ Mock servers ready${NC}"
echo ""

# Step 2: Install frontend dependencies
echo -e "${YELLOW}Step 2: Installing frontend dependencies...${NC}"
cd Frontend/admissions-chat
if [ ! -d "node_modules" ]; then
    npm install
else
    echo -e "${BLUE}Dependencies already installed${NC}"
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Creating .env.local...${NC}"
    cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_AGENT_PROXY_URL=http://localhost:3002
EOF
    echo -e "${GREEN}✓ Created .env.local${NC}"
else
    echo -e "${BLUE}.env.local already exists${NC}"
fi
cd ../..
echo -e "${GREEN}✓ Frontend ready${NC}"
echo ""

# Step 3: Start all services
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Starting Services${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

echo -e "${BLUE}This will open 3 terminal windows:${NC}"
echo "  1. Mock Form Submission API (http://localhost:3001)"
echo "  2. Mock Agent Proxy (http://localhost:3002)"
echo "  3. Frontend Dev Server (http://localhost:3000)"
echo ""
echo -e "${YELLOW}Press Ctrl+C in any window to stop that service${NC}"
echo ""
echo -e "${YELLOW}Starting in 3 seconds...${NC}"
sleep 3

# Detect OS and open terminals accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo -e "${BLUE}Opening terminals on macOS...${NC}"

    osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'/mock-servers\" && node form-submission.js"'
    sleep 1
    osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'/mock-servers\" && node agent-proxy.js"'
    sleep 1
    osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'/Frontend/admissions-chat\" && npm run dev"'

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo -e "${BLUE}Opening terminals on Linux...${NC}"

    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd mock-servers && node form-submission.js; exec bash"
        sleep 1
        gnome-terminal -- bash -c "cd mock-servers && node agent-proxy.js; exec bash"
        sleep 1
        gnome-terminal -- bash -c "cd Frontend/admissions-chat && npm run dev; exec bash"
    elif command -v konsole &> /dev/null; then
        konsole --new-tab -e bash -c "cd mock-servers && node form-submission.js; exec bash" &
        sleep 1
        konsole --new-tab -e bash -c "cd mock-servers && node agent-proxy.js; exec bash" &
        sleep 1
        konsole --new-tab -e bash -c "cd Frontend/admissions-chat && npm run dev; exec bash" &
    else
        echo -e "${YELLOW}Warning: Could not detect terminal emulator${NC}"
        echo "Please manually run these commands in 3 separate terminals:"
        echo "  1. cd mock-servers && node form-submission.js"
        echo "  2. cd mock-servers && node agent-proxy.js"
        echo "  3. cd Frontend/admissions-chat && npm run dev"
    fi

elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows Git Bash
    echo -e "${BLUE}Opening terminals on Windows...${NC}"

    start "Form API" cmd /k "cd mock-servers && node form-submission.js"
    sleep 1
    start "Agent Proxy" cmd /k "cd mock-servers && node agent-proxy.js"
    sleep 1
    start "Frontend" cmd /k "cd Frontend\admissions-chat && npm run dev"

else
    echo -e "${YELLOW}Unknown OS. Please manually run these commands:${NC}"
    echo "  1. cd mock-servers && node form-submission.js"
    echo "  2. cd mock-servers && node agent-proxy.js"
    echo "  3. cd Frontend/admissions-chat && npm run dev"
    exit 0
fi

sleep 3

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Services Started!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}URLs:${NC}"
echo "  Frontend:  http://localhost:3000"
echo "  Form API:  http://localhost:3001"
echo "  Agent API: http://localhost:3002"
echo ""
echo -e "${BLUE}Health Checks:${NC}"
echo "  curl http://localhost:3001/health"
echo "  curl http://localhost:3002/health"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Fill out the inquiry form"
echo "  3. Test the chat interface"
echo "  4. Try different prompts to see mock responses"
echo ""
echo -e "${GREEN}Happy Testing! 🚀${NC}"
