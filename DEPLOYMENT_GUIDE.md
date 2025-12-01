# AWS CDK Deployment Guide

## Infrastructure Overview

We have **ONE main CDK stack** that deploys everything:

### Stack: `AdmissionsAgentStack`

This single stack contains:

1. **Storage**:
   - S3 bucket for knowledge base documents
   - DynamoDB tables (WhatsappSessions, WhatsAppMessageTracking)

2. **Messaging**:
   - SQS queue for WhatsApp messages
   - SQS dead-letter queue

3. **Compute**:
   - Form Submission Lambda (Python 3.12)
   - WhatsApp Sender Lambda (Python 3.12)
   - Lambda layers (Salesforce, Twilio)

4. **API**:
   - API Gateway for form submission

5. **IAM**:
   - Execution roles for AgentCore
   - Lambda execution roles with appropriate permissions

## Prerequisites

✅ **Already Done** (I can see node_modules exists):
- Node.js installed
- npm dependencies installed

### Still Need:

1. **AWS CLI configured:**
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Default region: us-east-1
   # Default output format: json
   ```

2. **CDK Bootstrap** (one-time per AWS account/region):
   ```bash
   cd Backend/admissions-ai-agent
   npx cdk bootstrap
   ```

## Deployment Steps

### Step 1: Verify AWS Credentials

```bash
# Check your AWS credentials are configured
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-username"
# }
```

### Step 2: Build Lambda Layers (First Time Only)

The stack needs Python dependency layers for Salesforce and Twilio:

```bash
cd Backend/admissions-ai-agent

# Create Salesforce layer
mkdir -p layers/salesforce/python
pip install simple-salesforce requests -t layers/salesforce/python/

# Create Twilio layer
mkdir -p layers/twilio/python
pip install twilio -t layers/twilio/python/
```

### Step 3: Synthesize the CloudFormation Template

This generates the CloudFormation template without deploying:

```bash
cd Backend/admissions-ai-agent

# Synthesize (validate the stack)
npm run synth

# This should output:
# - CloudFormation template in cdk.out/
# - No errors
```

### Step 4: Review What Will Be Deployed

```bash
# Show the diff of what will be created
npx cdk diff

# This shows:
# - Resources to be created
# - IAM policies
# - Estimated costs (if available)
```

### Step 5: Deploy the Stack

```bash
# Deploy everything in one command
npm run deploy

# Or with explicit approval prompts:
npx cdk deploy --require-approval never

# Deployment takes 5-10 minutes
# You'll see:
# ✅ AdmissionsAgentStack: creating CloudFormation changeset...
# ✅ AdmissionsAgentStack: deploying...
# ✅ AdmissionsAgentStack: creating resources...
```

### Step 6: Save the Output Values

After deployment, CDK will output important values. **SAVE THESE**:

```bash
# Example outputs:
AdmissionsAgentStack.KnowledgeBaseBucketName = admissions-agent-kb-123456789012
AdmissionsAgentStack.FormSubmissionApiUrl = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod
AdmissionsAgentStack.SessionsTableName = WhatsappSessions
AdmissionsAgentStack.MessageTrackingTableName = WhatsAppMessageTracking
AdmissionsAgentStack.WhatsAppQueueUrl = https://sqs.us-east-1.amazonaws.com/123456789012/twilio-whatsapp-queue
```

## What Gets Deployed (In Order)

CDK automatically determines the correct deployment order based on dependencies:

1. **IAM Roles** (needed by other resources)
2. **S3 Bucket** (for knowledge base)
3. **DynamoDB Tables** (for session tracking)
4. **SQS Queues** (for message processing)
5. **Lambda Layers** (dependencies)
6. **Lambda Functions** (with layers attached)
7. **API Gateway** (with Lambda integration)

## Post-Deployment Configuration

### 1. Upload Test Knowledge Base Document

```bash
# Get your bucket name from outputs
BUCKET_NAME="admissions-agent-kb-123456789012"

# Create a test document
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

# Upload to S3
aws s3 cp test-kb-doc.txt s3://$BUCKET_NAME/test-kb-doc.txt
```

### 2. Create Bedrock Knowledge Base

**Option A: Via AWS Console (Easier for First Time)**

1. Go to AWS Console → Bedrock → Knowledge Bases
2. Click "Create knowledge base"
3. Name: `MapuaAdmissionsKB`
4. Data source: S3
5. S3 URI: `s3://admissions-agent-kb-123456789012/`
6. Embeddings model: Titan Embeddings G1 - Text
7. Vector store: Create new OpenSearch Serverless collection
8. Click "Create knowledge base"
9. Click "Sync" to ingest documents
10. **Save the Knowledge Base ID** (e.g., `XXXXXX`)

**Option B: Via AWS CLI**

```bash
# This is complex - use Console for first time
# See TESTING_WITHOUT_KB.md for CLI commands
```

### 3. Create Bedrock Memory

```bash
# Create memory for conversation history
aws bedrock-agent create-memory \
    --memory-name "MapuaAdmissionsMemory" \
    --memory-type "CONVERSATION" \
    --retention-days 90

# Save the Memory ID from output
```

### 4. Update Frontend Configuration

```bash
cd Frontend/admissions-chat

# Create .env.local with real endpoints
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod
NEXT_PUBLIC_AGENT_PROXY_URL=https://your-agent-lambda-function-url
EOF
```

## Dependency Installation (Already Done)

Since I can see `node_modules` exists, dependencies are already installed. But for reference:

### CDK Dependencies (TypeScript/Node.js)
- ✅ Already installed in `Backend/admissions-ai-agent/`
- Located in `node_modules/`
- Includes: `aws-cdk-lib`, `constructs`, etc.

### Lambda Dependencies (Python)
- ✅ Packaged in Lambda layers
- Salesforce layer: `simple-salesforce`, `requests`
- Twilio layer: `twilio`
- Lambda functions use these layers at runtime

### AgentCore Dependencies
- Installed separately when configuring AgentCore
- Located in `Backend/admissions-ai-agent/AgentCore/node_modules/`
- Installed via: `npm install` in AgentCore directory

## Common Issues & Solutions

### Issue 1: "CDK Bootstrap required"

```bash
# Solution: Bootstrap CDK in your account/region
npx cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Issue 2: "Layer creation failed - directory not found"

```bash
# Solution: Create Lambda layers first
cd Backend/admissions-ai-agent
mkdir -p layers/salesforce/python layers/twilio/python
pip install simple-salesforce requests -t layers/salesforce/python/
pip install twilio -t layers/twilio/python/
```

### Issue 3: "Insufficient permissions"

```bash
# Solution: Ensure your IAM user has these permissions:
# - AWSCloudFormationFullAccess
# - AmazonS3FullAccess
# - AmazonDynamoDBFullAccess
# - AWSLambda_FullAccess
# - IAMFullAccess
# - AmazonSQSFullAccess
# - AmazonAPIGatewayAdministrator
```

### Issue 4: "Python not found for layers"

```bash
# Solution: Install Python 3.12 and pip
# Windows: Download from python.org
# Mac: brew install python@3.12
# Linux: apt-get install python3.12 python3-pip
```

## Verification Commands

After deployment, verify everything is working:

```bash
# Check S3 bucket exists
aws s3 ls | grep admissions-agent-kb

# Check DynamoDB tables
aws dynamodb list-tables | grep -E "Whatsapp|MessageTracking"

# Check Lambda functions
aws lambda list-functions | grep -E "FormSubmission|WhatsAppSender"

# Check API Gateway
aws apigateway get-rest-apis

# Check SQS queues
aws sqs list-queues | grep whatsapp
```

## Cost Estimation

**Free Tier eligible resources:**
- Lambda: 1M requests/month free
- DynamoDB: 25GB storage free
- API Gateway: 1M requests/month free (12 months)

**Paid resources (minimal during testing):**
- S3: ~$0.023/GB/month
- OpenSearch Serverless (if using for KB): ~$0.24/OCU-hour
- Bedrock: ~$0.002/request

**Estimated monthly cost during testing: $5-20**

## Cleanup (When Done Testing)

```bash
# Destroy the entire stack
cd Backend/admissions-ai-agent
npx cdk destroy

# Note: S3 bucket and DynamoDB tables are set to RETAIN
# You'll need to manually delete them if desired:
aws s3 rb s3://admissions-agent-kb-123456789012 --force
aws dynamodb delete-table --table-name WhatsappSessions
aws dynamodb delete-table --table-name WhatsAppMessageTracking
```

## Next Steps After Deployment

1. ✅ Deploy CDK stack
2. ✅ Upload knowledge base documents
3. ✅ Create Bedrock Knowledge Base and sync
4. ✅ Create Bedrock Memory
5. Configure AgentCore (see `Backend/admissions-ai-agent/AgentCore/README.md`)
6. Deploy Agent
7. Update frontend with real API URLs
8. Test end-to-end flow

## Troubleshooting

### View CloudFormation Events
```bash
# If deployment fails, check events:
aws cloudformation describe-stack-events \
    --stack-name AdmissionsAgentStack \
    --max-items 20
```

### View Lambda Logs
```bash
# Check Lambda function logs
aws logs tail /aws/lambda/form-submission --follow
```

### Rollback
```bash
# If something goes wrong:
npx cdk destroy
# Fix the issue
# Re-deploy: npm run deploy
```

## Summary

**Single Stack Deployment:**
- One command: `npm run deploy`
- Deploys everything: S3, DynamoDB, Lambda, SQS, API Gateway
- Takes 5-10 minutes
- No manual ordering required (CDK handles dependencies)

**Key Points:**
- ✅ Dependencies already installed (I see node_modules)
- ⚠️ Need to create Lambda layers before deploying
- ⚠️ Need AWS CLI configured
- ⚠️ Need CDK bootstrap (one-time setup)
