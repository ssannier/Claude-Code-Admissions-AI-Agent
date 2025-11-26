# Quick Start Guide

Get the AI Admissions Agent running locally in 5 minutes!

---

## Option 1: Automatic Setup (Recommended)

Run the quick-start script:

```bash
./start-local-testing.sh
```

This will:
1. ✅ Install all dependencies
2. ✅ Create environment files
3. ✅ Start mock backend servers
4. ✅ Start frontend development server

Then open http://localhost:3000 in your browser!

---

## Option 2: Manual Setup

### Step 1: Install Mock Server Dependencies

```bash
cd mock-servers
npm install
```

### Step 2: Install Frontend Dependencies

```bash
cd ../Frontend/admissions-chat
npm install
```

### Step 3: Create Environment File

```bash
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_AGENT_PROXY_URL=http://localhost:3002
EOF
```

### Step 4: Start Services (3 terminals)

**Terminal 1 - Form API:**
```bash
cd mock-servers
node form-submission.js
```

**Terminal 2 - Agent Proxy:**
```bash
cd mock-servers
node agent-proxy.js
```

**Terminal 3 - Frontend:**
```bash
cd Frontend/admissions-chat
npm run dev
```

---

## What to Test

### 1. Form Submission
- Navigate to http://localhost:3000
- Fill out all form fields
- Submit and watch the transition to chat

### 2. Chat Interface
- Welcome message should appear
- Type: "What are the admission requirements?"
- Watch for:
  - 🔧 Tool indicator: "Using retrieve_university_info..."
  - 💬 Streaming response word-by-word
  - ✅ Final complete message

### 3. Different Prompts
Try these to see different mock responses:

- **Admission info**: "What are the requirements?"
- **Deadlines**: "When is the application deadline?"
- **Financial aid**: "Tell me about scholarships"
- **Campus info**: "What campuses do you have?"
- **Status check**: "What's my application status?"
- **Advisor handoff**: "Can I speak with an advisor?"

### 4. UI Features
- ✅ Regenerate button on AI messages
- ✅ Tool status indicators (yellow badge)
- ✅ Smooth auto-scrolling
- ✅ Message timestamps
- ✅ Loading states

---

## URLs

| Service | URL | Health Check |
|---------|-----|--------------|
| Frontend | http://localhost:3000 | Open in browser |
| Form API | http://localhost:3001 | http://localhost:3001/health |
| Agent API | http://localhost:3002 | http://localhost:3002/health |

---

## Troubleshooting

### Port Already in Use

If you see "EADDRINUSE" error:

```bash
# Find and kill the process
# On Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# On Mac/Linux:
lsof -ti:3000 | xargs kill -9
```

### Dependencies Not Installing

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules
npm install
```

### Frontend Not Connecting to Mock Servers

Check that `.env.local` exists in `Frontend/admissions-chat/` with:
```
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_AGENT_PROXY_URL=http://localhost:3002
```

---

## Next Steps

Once local testing works:

1. ✅ **Run Unit Tests** - See [TESTING_GUIDE.md](TESTING_GUIDE.md#local-testing)
2. ✅ **Deploy to AWS** - See [TESTING_GUIDE.md](TESTING_GUIDE.md#deployment-testing)
3. ✅ **End-to-End Tests** - See [TESTING_GUIDE.md](TESTING_GUIDE.md#end-to-end-testing)

---

## Full Documentation

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Complete testing strategy
- **[IMPLEMENTATION_AUDIT_REPORT.md](IMPLEMENTATION_AUDIT_REPORT.md)** - Implementation status
- **[ARCHITECTURE_COMPLIANCE_AUDIT.md](ARCHITECTURE_COMPLIANCE_AUDIT.md)** - Architecture compliance

---

**Happy Testing! 🚀**
