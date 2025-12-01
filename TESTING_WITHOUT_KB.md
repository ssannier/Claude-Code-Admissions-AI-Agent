# Testing Guide: Without Knowledge Base Data

This guide helps you test the AI Admissions Agent infrastructure before you have real knowledge base documents.

## What We Can Test Now

### 1. AWS Infrastructure Deployment ✅
- DynamoDB tables
- Lambda functions
- API Gateway endpoints
- S3 buckets (empty for now)
- Basic AgentCore configuration

### 2. Frontend → Backend Integration ✅
- Form submission to API Gateway
- Session creation and management
- SSE streaming connection
- Error handling

### 3. AgentCore with Placeholder Knowledge Base ✅
- Basic conversational flow
- Memory management
- Tool orchestration (without real KB data)
- Streaming responses

## Step-by-Step Testing Plan

### Step 1: Deploy AWS Infrastructure

```bash
cd Backend/admissions-ai-agent

# Install dependencies
npm install

# Configure AWS credentials (if not already done)
aws configure

# Deploy the stack
npm run deploy
```

**What this deploys:**
- DynamoDB tables: `WhatsappSessions`, `WhatsAppMessageTracking`
- S3 bucket for knowledge base (can be empty)
- Lambda functions with placeholder configurations
- API Gateway for form submission

**Expected Output:**
- Stack deployment succeeds
- You get API Gateway URL and Lambda Function URLs
- CloudFormation outputs show all resource ARNs

### Step 2: Create Placeholder Knowledge Base

Even without real data, create a simple text file to test the KB integration:

```bash
# Create a simple test document
cat > test-kb-doc.txt << 'EOF'
Mapua University Admissions Information

Programs:
- Undergraduate: Engineering, Computer Science, Architecture
- Graduate: MBA, MS Engineering, MS Computer Science
- Senior High School: STEM, ABM tracks
- Fully Online: Various programs available

Admission Requirements:
- High school diploma or equivalent
- Minimum GPA requirements vary by program
- Standardized test scores (if applicable)
- Letters of recommendation
- Personal statement

Financial Aid:
- Scholarships available for qualified students
- Merit-based and need-based options
- Contact admissions office for details

Contact:
- Email: admissions@mapua.edu.ph
- Phone: +63-2-8247-5000
EOF

# Upload to S3 (replace bucket name with your actual bucket)
aws s3 cp test-kb-doc.txt s3://YOUR-KB-BUCKET-NAME/test-kb-doc.txt
```

### Step 3: Configure AgentCore (Without Salesforce/Twilio)

For now, we'll configure AgentCore to work WITHOUT external integrations:

```bash
cd Backend/admissions-ai-agent/AgentCore

# Install dependencies
npm install

# Create minimal .env file
cat > .env << 'EOF'
# AWS Configuration
AWS_REGION=us-east-1
KNOWLEDGE_BASE_ID=your-kb-id-here
MEMORY_ID=your-memory-id-here

# Disable external integrations for testing
ENABLE_SALESFORCE=false
ENABLE_TWILIO=false

# Agent Configuration
AGENT_ID=your-agent-id-here
AGENT_ALIAS_ID=TSTALIASID
EOF

# Configure AgentCore
npx agentcore configure
```

**During configuration:**
1. Choose Claude Sonnet 4.5 as model
2. Skip Salesforce tool configuration (we'll add later)
3. Skip Twilio/WhatsApp tool configuration
4. Configure Knowledge Base tool with your KB ID
5. Enable Bedrock Memory with your Memory ID

### Step 4: Test Form Submission

Update frontend to point to real API:

```bash
cd Frontend/admissions-chat

# Create .env.local with real endpoints
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=https://your-api-gateway-url
NEXT_PUBLIC_AGENT_PROXY_URL=https://your-agent-lambda-url
EOF

# Start frontend
npm run dev
```

**Test Flow:**
1. Open http://localhost:3000
2. Fill out inquiry form
3. Submit form
4. Verify:
   - Form submission succeeds
   - You're redirected to chat page
   - Session is created in DynamoDB

### Step 5: Test Basic Chat (Without Real KB Responses)

With AgentCore configured but limited KB:

**Expected Behavior:**
- Agent responds with conversational flow
- Streaming works (you see text appear gradually)
- Agent attempts to search KB (may return limited info from placeholder doc)
- Memory tracks conversation history
- No errors in console

**Test Prompts:**
1. "What programs do you offer?" → Should return info from placeholder doc
2. "Tell me about scholarships" → Should return info from placeholder doc
3. "I'd like to speak with someone" → Should offer advisor handoff (but won't actually work yet)

### Step 6: Verify Infrastructure Components

```bash
# Check DynamoDB tables
aws dynamodb scan --table-name WhatsappSessions --max-items 5
aws dynamodb scan --table-name WhatsAppMessageTracking --max-items 5

# Check S3 bucket
aws s3 ls s3://YOUR-KB-BUCKET-NAME/

# Check Lambda logs
aws logs tail /aws/lambda/agent-proxy --follow
aws logs tail /aws/lambda/form-submission --follow

# Check Bedrock Knowledge Base status
aws bedrock-agent get-knowledge-base --knowledge-base-id YOUR-KB-ID
```

## What Works vs. What Doesn't (Yet)

### ✅ Should Work Now:
1. Form submission and validation
2. Session creation and tracking
3. Basic conversational flow
4. Streaming responses
5. Memory management (conversation history)
6. Knowledge Base search (with placeholder data)
7. Error handling and display
8. Frontend UI and navigation

### ❌ Won't Work Until Real Data:
1. Accurate responses about specific programs
2. Detailed admission requirements
3. Financial aid information
4. Campus-specific details

### ❌ Won't Work Until External Integrations:
1. Salesforce Lead creation
2. Advisor handoff (Salesforce Task creation)
3. WhatsApp notifications
4. Actual advisor contact

## Troubleshooting Common Issues

### Issue: "Knowledge Base not found"
**Solution:** Make sure you've created the KB in Bedrock and synced it (even if empty)

### Issue: "No streaming responses"
**Solution:** Check Lambda function URL is correct in .env.local, verify CORS settings

### Issue: "Form submission fails"
**Solution:** Check API Gateway URL is correct, verify CORS configuration in CDK stack

### Issue: "Agent doesn't respond"
**Solution:** Check AgentCore configuration, verify model permissions in IAM

### Issue: "Memory not persisting"
**Solution:** Verify Memory ID is correct, check DynamoDB tables exist

## Next Steps When You Get Real Data

1. **Upload Knowledge Base Documents:**
   ```bash
   aws s3 sync /path/to/real/docs s3://YOUR-KB-BUCKET-NAME/
   aws bedrock-agent start-ingestion-job --knowledge-base-id YOUR-KB-ID
   ```

2. **Configure External Integrations:**
   - Set up Salesforce credentials in Secrets Manager
   - Set up Twilio credentials in Secrets Manager
   - Update AgentCore configuration to enable tools
   - Redeploy agent

3. **Test Complete Flow:**
   - Full conversation with accurate responses
   - Advisor handoff creates Salesforce Task
   - WhatsApp notification sends successfully

## Monitoring and Logging

### CloudWatch Logs:
```bash
# Agent Proxy logs
aws logs tail /aws/lambda/agent-proxy --follow

# Form Submission logs
aws logs tail /aws/lambda/form-submission --follow

# WhatsApp Sender logs (when enabled)
aws logs tail /aws/lambda/whatsapp-sender --follow
```

### DynamoDB Queries:
```bash
# Check all sessions
aws dynamodb scan --table-name WhatsappSessions

# Check specific session
aws dynamodb get-item \
  --table-name WhatsappSessions \
  --key '{"session_id": {"S": "YOUR-SESSION-ID"}}'
```

### Bedrock Metrics:
- Go to AWS Console → Bedrock → Agents
- View your agent's invocation metrics
- Check knowledge base query metrics

## Cost Estimation (Testing Phase)

**Without heavy usage:**
- DynamoDB: ~$1-2/month (on-demand)
- Lambda: ~$0.20 per 1M requests (testing should be minimal)
- Bedrock Agent: ~$0.002 per request
- S3: ~$0.023 per GB/month (minimal for small KB)
- **Total: ~$5-10/month for testing**

## Safety Notes

⚠️ **Important:**
1. Don't commit real credentials to git
2. Use AWS Secrets Manager for sensitive data
3. Set up AWS Cost Alerts (e.g., alert at $20/month)
4. Delete test data regularly from DynamoDB
5. Monitor CloudWatch for errors

## When You're Ready for Production

- [ ] Real knowledge base documents uploaded
- [ ] Salesforce integration configured
- [ ] Twilio WhatsApp configured
- [ ] All environment variables in Secrets Manager
- [ ] Error monitoring set up (CloudWatch Alarms)
- [ ] Cost alerts configured
- [ ] Load testing completed
- [ ] Security review completed
- [ ] Documentation updated
