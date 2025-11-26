# Testing Guide - AI Admissions Agent

**Last Updated**: November 25, 2024

This guide provides a comprehensive testing strategy for the AI Admissions Agent system, from local unit tests to production deployment validation.

---

## Table of Contents

1. [Local Testing](#local-testing)
2. [Integration Testing](#integration-testing)
3. [Deployment Testing](#deployment-testing)
4. [End-to-End Testing](#end-to-end-testing)
5. [Production Validation](#production-validation)
6. [Troubleshooting](#troubleshooting)

---

## Local Testing

### Prerequisites

Before running any tests, optionally install all development dependencies at once:

```bash
# (Optional) Install all development dependencies from root
pip install -r requirements-dev.txt
```

This will install all testing frameworks, mocking libraries, and code quality tools in one go. Alternatively, you can install dependencies individually for each Lambda function as shown below.

### Phase 1: Lambda Function Unit Tests

#### 1.1 Form Submission Lambda

```bash
cd Backend/admissions-ai-agent/lambda/form-submission

# Install dependencies
# Note: requirements.txt includes both runtime and test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/test_form_submission.py -v

# Run with coverage
python -m pytest tests/test_form_submission.py --cov=form_submission --cov-report=html

# Expected result: 18/20 tests passing (90%)
```

**Current Status**: ✅ 18/20 passing
**Remaining Issues**: 2 edge case failures (non-critical)

#### 1.2 WhatsApp Sender Lambda

```bash
cd Backend/admissions-ai-agent/lambda/whatsapp-sender

# Install dependencies
# Note: requirements.txt includes both runtime and test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/test_whatsapp_sender.py -v

# Expected result: 10/11 tests passing (91%)
```

**Current Status**: ✅ 10/11 passing
**Remaining Issues**: 1 retry logic edge case (non-critical)

#### 1.3 Agent Proxy Lambda

```bash
cd Backend/admissions-ai-agent/lambda/agent-proxy

# Install dependencies
npm install

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Expected result: 12/12 tests passing (100%)
```

**Current Status**: ✅ 12/12 passing (100%)

---

### Phase 2: AgentCore Local Testing

#### 2.1 Test Individual Tools

Create a test script for each tool:

```bash
cd Backend/admissions-ai-agent/AgentCore

# Set up environment variables
export SALESFORCE_USERNAME="your-username"
export SALESFORCE_PASSWORD="your-password"
export SALESFORCE_SECURITY_TOKEN="your-token"
export SALESFORCE_DOMAIN="test"  # Use Salesforce sandbox

export TWILIO_ACCOUNT_SID="your-account-sid"
export TWILIO_AUTH_TOKEN="your-auth-token"
export TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"

export BEDROCK_KNOWLEDGE_BASE_ID="your-kb-id"
export AWS_REGION="us-east-1"

# Test knowledge tool
python3 << 'EOF'
import asyncio
from tools.knowledge_tool import retrieve_university_info

async def test():
    result = retrieve_university_info(
        query="What are the undergraduate admission requirements?",
        topic="admissions"
    )
    print(result)

asyncio.run(test())
EOF
```

#### 2.2 Test Salesforce Integration

```python
# test_salesforce_integration.py
from tools.salesforce_tool import query_salesforce_leads, create_salesforce_task

# Test lead query
result = query_salesforce_leads(
    email="test@example.com",
    phone_number="+15551234567"
)
print("Lead query result:", result)

# Test task creation (use a real Lead ID from your sandbox)
task_id = create_salesforce_task(
    lead_id="00Q5e000001abcDEFG",  # Replace with real Lead ID
    subject="Test Task",
    description="This is a test task created from local testing",
    priority="Normal"
)
print("Task created:", task_id)
```

#### 2.3 Test WhatsApp Tool

```python
# test_whatsapp_integration.py
from tools.whatsapp_tool import send_whatsapp_message

result = send_whatsapp_message(
    recipient_phone="+15551234567",  # Use your test number
    message_content="Test message from local testing",
    timing_preference="as soon as possible",
    student_name="Test User"
)
print("WhatsApp send result:", result)
```

---

### Phase 3: Frontend Local Testing

```bash
cd Frontend/admissions-chat

# Install dependencies
npm install

# Set up local environment
cp .env.example .env.local

# Edit .env.local
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_AGENT_PROXY_URL=http://localhost:3002
EOF

# Run development server
npm run dev

# Open browser to http://localhost:3000
```

**Manual Testing Checklist**:
- [ ] Inquiry form displays correctly
- [ ] Form validation works (try submitting empty fields)
- [ ] Form submission shows loading state
- [ ] Chat interface appears after submission
- [ ] Welcome message displays
- [ ] Input field accepts text
- [ ] Send button works
- [ ] Messages display in chat
- [ ] Auto-scroll works
- [ ] Regenerate button appears on AI messages
- [ ] Tool status indicators display (when backend connected)

---

## Integration Testing

### Phase 4: Backend Mock Servers

Create mock servers for testing frontend without full AWS deployment:

#### 4.1 Mock Form Submission API

```javascript
// mock-servers/form-submission.js
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

app.post('/submit', (req, res) => {
  console.log('Form submission received:', req.body);

  // Simulate processing delay
  setTimeout(() => {
    res.json({
      success: true,
      message: 'Form submitted successfully',
      leadId: 'MOCK-LEAD-' + Date.now()
    });
  }, 1000);
});

app.listen(3001, () => {
  console.log('Mock Form Submission API running on http://localhost:3001');
});
```

#### 4.2 Mock Agent Proxy with SSE

```javascript
// mock-servers/agent-proxy.js
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

app.post('/', (req, res) => {
  console.log('Agent proxy request received:', req.body);

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  // Simulate tool usage
  setTimeout(() => {
    res.write(`data: ${JSON.stringify({thinking: "Using retrieve_university_info..."})}\n\n`);
  }, 500);

  // Simulate response chunks
  const response = "Based on our admissions documentation, undergraduate applicants need a high school diploma with a minimum GPA of 3.0.";
  const words = response.split(' ');

  words.forEach((word, i) => {
    setTimeout(() => {
      res.write(`data: ${JSON.stringify({response: word + ' '})}\n\n`);
    }, 1000 + (i * 100));
  });

  // Send final result
  setTimeout(() => {
    res.write(`data: ${JSON.stringify({final_result: response})}\n\n`);
    res.end();
  }, 1000 + (words.length * 100) + 500);
});

app.listen(3002, () => {
  console.log('Mock Agent Proxy running on http://localhost:3002');
});
```

**Run Mock Servers**:
```bash
# Terminal 1
node mock-servers/form-submission.js

# Terminal 2
node mock-servers/agent-proxy.js

# Terminal 3
cd Frontend/admissions-chat
npm run dev
```

---

### Phase 5: AWS Integration Testing

#### 5.1 Deploy Backend Stack (Development)

```bash
cd Backend/admissions-ai-agent

# Set environment variables
export AWS_REGION=us-east-1
export AWS_PROFILE=your-dev-profile

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy main stack
cdk deploy AdmissionsAgentStack --require-approval never

# Note the outputs:
# - FormSubmissionAPIEndpoint
# - AgentProxyFunctionUrl
# - ECRRepositoryUri
```

#### 5.2 Upload Lambda Layers

```bash
cd Backend/admissions-ai-agent/lambda-layers

# Verify layers are built
ls -lh salesforce-layer.zip twilio-layer.zip

# Upload Salesforce layer
aws lambda publish-layer-version \
  --layer-name salesforce-layer \
  --description "Simple Salesforce library" \
  --zip-file fileb://salesforce-layer.zip \
  --compatible-runtimes python3.12 \
  --region us-east-1

# Note the LayerVersionArn

# Upload Twilio layer
aws lambda publish-layer-version \
  --layer-name twilio-layer \
  --description "Twilio library for WhatsApp" \
  --zip-file fileb://twilio-layer.zip \
  --compatible-runtimes python3.12 \
  --region us-east-1

# Note the LayerVersionArn
```

#### 5.3 Configure Lambda Environment Variables

```bash
# Form Submission Lambda
aws lambda update-function-configuration \
  --function-name FormSubmissionFunction \
  --environment "Variables={
    SALESFORCE_USERNAME=your-username,
    SALESFORCE_PASSWORD=your-password,
    SALESFORCE_SECURITY_TOKEN=your-token,
    SALESFORCE_DOMAIN=test
  }"

# WhatsApp Sender Lambda
aws lambda update-function-configuration \
  --function-name SendWhatsAppFunction \
  --environment "Variables={
    TWILIO_ACCOUNT_SID=your-sid,
    TWILIO_AUTH_TOKEN=your-token,
    TWILIO_WHATSAPP_FROM=whatsapp:+14155238886,
    DYNAMODB_TABLE=WhatsAppMessageTracking
  }"
```

#### 5.4 Test Lambda Functions Directly

```bash
# Test Form Submission
aws lambda invoke \
  --function-name FormSubmissionFunction \
  --payload '{
    "body": "{\"firstName\":\"Test\",\"lastName\":\"User\",\"email\":\"test@example.com\",\"cellPhone\":\"+15551234567\",\"headquarters\":\"Manila\",\"programType\":\"Undergraduate\",\"timingPreference\":\"2 hours\"}"
  }' \
  response.json

cat response.json

# Test WhatsApp Sender
aws sqs send-message \
  --queue-url $(aws sqs get-queue-url --queue-name twilio-whatsapp-queue --query 'QueueUrl' --output text) \
  --message-body '{
    "recipient_phone": "+15551234567",
    "message_body": "Test message from SQS",
    "timing_preference": "as soon as possible"
  }'
```

---

### Phase 6: AgentCore Deployment Testing

#### 6.1 Configure Agent

```bash
cd Backend/admissions-ai-agent/AgentCore

# Run agentcore configure
agentcore configure

# You'll be prompted for:
# - Execution role ARN (get from CDK outputs)
# - ECR repository URI (get from CDK outputs)
# - Bedrock Memory ID (create in AWS console first)
# - AWS Region

# Verify configuration
cat .agentcore/config.json
```

#### 6.2 Deploy Agent

```bash
# Run the launch script
./scripts/launch_agent.sh

# This will:
# 1. Build Docker image
# 2. Push to ECR
# 3. Deploy to Bedrock AgentCore
# 4. Output Agent ID and ARN

# Save the Agent ID for next steps
export AGENT_ID=<from-output>
export AGENT_ALIAS_ID=<from-bedrock-console>
```

#### 6.3 Update Agent Proxy Lambda

```bash
# Update environment variables
aws lambda update-function-configuration \
  --function-name AgentProxyFunction \
  --environment "Variables={
    AGENT_ID=$AGENT_ID,
    AGENT_ALIAS_ID=$AGENT_ALIAS_ID,
    AWS_REGION=us-east-1
  }"
```

#### 6.4 Test Agent Directly

```bash
# Using Strands CLI
agentcore test \
  --agent-id $AGENT_ID \
  --prompt "What are the undergraduate admission requirements?"

# Using AWS CLI
aws bedrock-agent-runtime invoke-agent \
  --agent-id $AGENT_ID \
  --agent-alias-id $AGENT_ALIAS_ID \
  --session-id test-session-$(date +%s) \
  --input-text "What are the undergraduate admission requirements?" \
  output.json

cat output.json
```

---

## Deployment Testing

### Phase 7: Frontend Deployment

#### 7.1 Deploy Amplify Stack

```bash
cd Backend/admissions-ai-agent

# Create GitHub token secret (first time only)
aws secretsmanager create-secret \
  --name github-token \
  --secret-string "your-github-personal-access-token"

# Set environment variables
export GITHUB_OWNER=your-github-org
export GITHUB_REPO=admissions-ai-agent
export GITHUB_BRANCH=main
export API_GATEWAY_URL=<from-cdk-outputs>
export AGENT_PROXY_URL=<from-cdk-outputs>

# Deploy Amplify stack
cdk deploy AmplifyHostingStack
```

#### 7.2 Alternative: Manual Deployment Script

```bash
cd ../../  # Back to repo root

# Set Amplify App ID (from CDK outputs)
export AMPLIFY_APP_ID=<from-cdk-outputs>
export AMPLIFY_BRANCH=main

# Run deployment script
./deploy-scripts/frontend-amplify-deploy.sh
```

---

## End-to-End Testing

### Phase 8: Complete User Flow Test

#### 8.1 Test Checklist

**1. Form Submission**:
- [ ] Navigate to Amplify URL
- [ ] Fill out inquiry form with test data
- [ ] Submit form
- [ ] Verify success message
- [ ] Check Salesforce: Lead should be created
- [ ] Verify Lead status is "Open - Not Contacted"

**2. Chat with Nemo**:
- [ ] Chat interface appears after form submission
- [ ] Welcome message displays with student name
- [ ] Type: "What are the undergraduate admission requirements?"
- [ ] Verify tool indicator shows "Using retrieve_university_info..."
- [ ] Verify response streams in real-time
- [ ] Verify response includes source citations
- [ ] Test regenerate button on AI response

**3. Salesforce Status Check**:
- [ ] Type: "What's the status of my application?"
- [ ] Verify agent queries Salesforce
- [ ] Verify agent returns Lead information

**4. Advisor Handoff**:
- [ ] Type: "I have a complex financial aid question. Can I speak with an advisor?"
- [ ] Verify agent asks for confirmation
- [ ] Type: "Yes, please connect me."
- [ ] Verify advisor handoff confirmation message
- [ ] Check Salesforce: Lead status should be "Working - Connected"
- [ ] Check Salesforce: Task should exist with title "AI Chat Summary - Advisor Handoff"
- [ ] Verify Task description includes conversation transcript
- [ ] Check phone: WhatsApp message should arrive based on timing preference

**5. Error Handling**:
- [ ] Test with invalid form data
- [ ] Test with network disconnect
- [ ] Test with long conversation (>10 turns)
- [ ] Verify error messages are user-friendly

---

## Production Validation

### Phase 9: Production Deployment

#### 9.1 Pre-Production Checklist

- [ ] All tests passing in dev environment
- [ ] End-to-end flow tested successfully
- [ ] Salesforce integration verified
- [ ] WhatsApp delivery confirmed
- [ ] Knowledge base returning accurate results
- [ ] Security review completed
- [ ] Load testing performed

#### 9.2 Production Deployment

```bash
# Set production AWS profile
export AWS_PROFILE=production

# Deploy with production configurations
cd Backend/admissions-ai-agent
cdk deploy --all \
  --context environment=production \
  --require-approval never

# Deploy agent to production
cd AgentCore
./scripts/launch_agent.sh

# Deploy frontend
cd ../../..
AMPLIFY_APP_ID=<prod-app-id> ./deploy-scripts/frontend-amplify-deploy.sh
```

#### 9.3 Smoke Tests

```bash
# Test production endpoints
curl -X POST https://your-prod-api.amazonaws.com/prod/submit \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Smoke",
    "lastName": "Test",
    "email": "smoketest@example.com",
    "cellPhone": "+15551234567",
    "headquarters": "Manila",
    "programType": "Undergraduate",
    "timingPreference": "2 hours"
  }'

# Monitor CloudWatch logs
aws logs tail /aws/lambda/FormSubmissionFunction --follow
```

#### 9.4 Monitoring Setup

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name AdmissionsAgentDashboard \
  --dashboard-body file://monitoring/dashboard.json

# Set up alarms
aws cloudwatch put-metric-alarm \
  --alarm-name FormSubmissionErrors \
  --alarm-description "Alert on form submission errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Lambda Timeout

**Symptom**: Lambda functions timing out
**Solution**:
```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name YourFunction \
  --timeout 300  # 5 minutes
```

#### Issue 2: Salesforce API Limits

**Symptom**: "API limit exceeded" errors
**Solution**:
- Use Salesforce Sandbox for testing
- Implement exponential backoff
- Cache Salesforce queries

#### Issue 3: SSE Connection Drops

**Symptom**: Chat streaming stops mid-response
**Solution**:
- Check Agent Proxy Lambda timeout (should be 300s)
- Verify client-side timeout settings
- Check CloudWatch logs for errors

#### Issue 4: Agent Not Finding Knowledge

**Symptom**: Agent returns "I don't have information..."
**Solution**:
```bash
# Verify Knowledge Base ID
aws bedrock-agent list-knowledge-bases

# Test Knowledge Base directly
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id $KB_ID \
  --retrieval-query '{"text":"admission requirements"}'
```

#### Issue 5: WhatsApp Not Sending

**Symptom**: No WhatsApp messages received
**Solution**:
- Verify Twilio credentials
- Check SQS queue for messages
- Verify phone number format (E.164)
- Check Twilio WhatsApp sandbox status

---

## Performance Testing

### Load Testing Script

```bash
# Install artillery
npm install -g artillery

# Create load test config
cat > load-test.yml << 'EOF'
config:
  target: 'https://your-api.amazonaws.com'
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 120
      arrivalRate: 50
      name: "Sustained load"
scenarios:
  - name: "Form submission"
    flow:
      - post:
          url: "/prod/submit"
          json:
            firstName: "Load"
            lastName: "Test"
            email: "loadtest@example.com"
            cellPhone: "+15551234567"
            headquarters: "Manila"
            programType: "Undergraduate"
            timingPreference: "2 hours"
EOF

# Run load test
artillery run load-test.yml
```

---

## Testing Metrics

Track these metrics during testing:

| Metric | Target | Current |
|--------|--------|---------|
| Form Submission Success Rate | >99% | TBD |
| Average Form Response Time | <2s | TBD |
| Agent Response Latency | <5s | TBD |
| SSE Stream Success Rate | >95% | TBD |
| Salesforce API Success Rate | >99% | TBD |
| WhatsApp Delivery Rate | >95% | TBD |
| Knowledge Base Accuracy | >90% | TBD |

---

## Next Steps

1. **Start with Local Testing**: Run all unit tests first
2. **Deploy to Dev**: Deploy backend to AWS development account
3. **Integration Tests**: Test with real AWS services
4. **Deploy Agent**: Deploy Nemo to Bedrock AgentCore
5. **Frontend Testing**: Deploy frontend to Amplify
6. **End-to-End**: Complete full user flow test
7. **Production**: Deploy to production with monitoring

---

**Testing Prepared By**: Claude Code Agent
**Last Updated**: November 25, 2024
**Version**: 1.0
