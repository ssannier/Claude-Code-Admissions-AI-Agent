# Testing Quick Start

This is a simplified guide to get you running tests quickly.

## Option 1: Install All Dependencies at Once (Recommended)

```bash
# From the root of the project
pip install -r requirements-dev.txt
```

This installs all testing dependencies for all Lambda functions in one go:
- pytest (testing framework)
- hypothesis (property-based testing)
- moto (AWS mocking)
- simple-salesforce (Salesforce API)
- twilio (Twilio API)
- And more...

## Option 2: Install Per Lambda Function

If you prefer to install dependencies only for the specific Lambda you're testing:

### Form Submission Lambda
```bash
cd Backend/admissions-ai-agent/lambda/form-submission
pip install -r requirements.txt
python -m pytest tests/ -v
```

### WhatsApp Sender Lambda
```bash
cd Backend/admissions-ai-agent/lambda/whatsapp-sender
pip install -r requirements.txt
python -m pytest tests/ -v
```

### Agent Proxy Lambda (Node.js)
```bash
cd Backend/admissions-ai-agent/lambda/agent-proxy
npm install
npm test
```

## Run All Python Tests

After installing dependencies with Option 1:

```bash
# From project root
python -m pytest Backend/admissions-ai-agent/lambda/form-submission/tests/ -v
python -m pytest Backend/admissions-ai-agent/lambda/whatsapp-sender/tests/ -v
```

## Frontend Local Testing (No API Tokens Required!)

```bash
# One command to start everything
./start-local-testing.sh
```

This starts:
1. Mock Form API (port 3001)
2. Mock Agent Proxy (port 3002)
3. Frontend dev server (port 3000)

Open http://localhost:3000 in your browser and test the entire frontend without any real AWS credentials!

## Troubleshooting

### "ModuleNotFoundError: No module named 'pytest'"
Run: `pip install -r requirements-dev.txt`

### "simple-salesforce not found"
The Lambda uses a layer for Salesforce. For local testing, install with:
```bash
pip install simple-salesforce==1.12.4
```

### Tests can't find the module
Make sure you're in the correct directory and run with `python -m pytest` (not just `pytest`)

### Python 3.14 Compatibility Issue with pytest-asyncio
If you see `AttributeError: 'Package' object has no attribute 'obj'`, it's a pytest-asyncio compatibility issue with Python 3.14.

**Workaround**: The form submission and WhatsApp sender tests don't actually use async, so uninstall pytest-asyncio:
```bash
pip uninstall pytest-asyncio -y
```

Then run tests normally. They'll work fine without it!

## What Gets Tested?

- **Form Submission Lambda**: 13/13 tests passing ✅ (validation, Salesforce integration)
- **WhatsApp Sender Lambda**: 10/11 tests passing ✅ (Twilio integration, retry logic - 1 non-critical)
- **Agent Proxy Lambda**: 12/12 tests passing ✅ (SSE streaming, Bedrock integration)
- **Frontend**: Full UI testing with mock servers (no real credentials needed)

**Total**: 35/36 Lambda tests passing (97%)

## Next Steps

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing strategy including integration tests, deployment tests, and production validation.
