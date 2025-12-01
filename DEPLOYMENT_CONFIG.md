# Deployment Configuration

**Last Updated**: 2025-11-30
**Region**: us-west-2
**AWS Account**: 756493389182

## Infrastructure Resources (CDK Stack)

### S3 Buckets
- **Knowledge Base Bucket**: `admissions-agent-kb-756493389182-us-west-2`
  - Region: us-west-2
  - Contains: Knowledge base documents for AI agent

### DynamoDB Tables
- **Sessions Table**: `WhatsappSessions`
- **Message Tracking Table**: `WhatsAppMessageTracking`

### SQS Queues
- **WhatsApp Queue**: `https://sqs.us-west-2.amazonaws.com/756493389182/twilio-whatsapp-queue`
- **WhatsApp DLQ**: `https://sqs.us-west-2.amazonaws.com/756493389182/twilio-whatsapp-dlq`

### Lambda Functions
- **Agent Proxy**: `admissions-agent-proxy`
  - Function URL: `https://56esu4j6ukmbjfwzqoml7jsjvq0uwrdw.lambda-url.us-west-2.on.aws/`
  - Purpose: Streams AI agent responses via SSE
- **Form Submission**: `admissions-form-submission`
- **WhatsApp Sender**: `admissions-whatsapp-sender`

### API Gateway
- **API Name**: Admissions Form API
- **API ID**: 9ppnenaq01
- **Base URL**: `https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod/`
- **Form Submission Endpoint**: `https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod/submit`

### ECR Repository
- **Repository**: `756493389182.dkr.ecr.us-west-2.amazonaws.com/admissions-agent`

### IAM Roles
- **Agent Execution Role**: `arn:aws:iam::756493389182:role/AdmissionsAgentExecutionRole`

## Bedrock Resources

### Knowledge Base
- **Name**: AIAdmissionsKnowledgeBase
- **Knowledge Base ID**: `W4BL49Y7MZ`
- **Data Source ID**: `R84WZU7YSI`
- **Data Source Name**: AdmissionsDocuments
- **Status**: ACTIVE
- **S3 Bucket**: admissions-agent-kb-756493389182-us-west-2

### OpenSearch Serverless
- **Collection Name**: bedrock-knowledge-base-mj4p1m
- **Collection ARN**: `arn:aws:aoss:us-west-2:756493389182:collection/cag5pwhzf3ywgfpk7lx7`
- **Index Name**: bedrock-knowledge-base-default-index
- **Vector Field**: bedrock-knowledge-base-default-vector

### Bedrock Memory
- **Memory Type**: SESSION_SUMMARY (managed by Strands SDK)
- **Memory ID**: To be generated per session

## Environment Variables for AgentCore

```bash
# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=756493389182

# Bedrock Configuration
KNOWLEDGE_BASE_ID=W4BL49Y7MZ
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
MODEL_TEMPERATURE=0.7

# DynamoDB Tables
SESSIONS_TABLE_NAME=WhatsappSessions
MESSAGE_TRACKING_TABLE=WhatsAppMessageTracking

# SQS Queues
WHATSAPP_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/756493389182/twilio-whatsapp-queue

# External Integrations (set via secrets)
SF_USERNAME=<from-secrets>
SF_PASSWORD=<from-secrets>
SF_TOKEN=<from-secrets>
TWILIO_ACCOUNT_SID=<from-secrets>
TWILIO_AUTH_TOKEN=<from-secrets>
TWILIO_PHONE_NUMBER=<from-secrets>

# Logging
LOG_LEVEL=INFO
```

## Frontend Environment Variables

```bash
# API Endpoints
NEXT_PUBLIC_API_URL=https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod
NEXT_PUBLIC_FORM_SUBMISSION_URL=https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod/submit
NEXT_PUBLIC_AGENT_PROXY_URL=https://56esu4j6ukmbjfwzqoml7jsjvq0uwrdw.lambda-url.us-west-2.on.aws/
```

## Deployment Commands

### Deploy CDK Stack
```bash
cd Backend/admissions-ai-agent
npx cdk deploy
```

### Sync Knowledge Base
```bash
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id W4BL49Y7MZ \
  --data-source-id R84WZU7YSI \
  --region us-west-2
```

### Deploy AgentCore
```bash
cd Backend/admissions-ai-agent/AgentCore
# Build and push Docker image
docker build -t admissions-agent .
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 756493389182.dkr.ecr.us-west-2.amazonaws.com
docker tag admissions-agent:latest 756493389182.dkr.ecr.us-west-2.amazonaws.com/admissions-agent:latest
docker push 756493389182.dkr.ecr.us-west-2.amazonaws.com/admissions-agent:latest

# Deploy with agentcore CLI
agentcore launch \
  --name admissions-agent \
  --image 756493389182.dkr.ecr.us-west-2.amazonaws.com/admissions-agent:latest \
  --role arn:aws:iam::756493389182:role/AdmissionsAgentExecutionRole \
  --region us-west-2
```

### Deploy Frontend
```bash
cd Frontend/admissions-chat
npm run build
# Deploy to Amplify or Vercel
```

## Testing

### Test Knowledge Base Retrieval
```bash
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id W4BL49Y7MZ \
  --retrieval-query text="What are the admission requirements?" \
  --region us-west-2
```

### Test Form Submission API
```bash
curl -X POST https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod/submit \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Student",
    "email": "test@example.com",
    "phone": "+15551234567",
    "program_interest": "Graduate",
    "campus_preference": "Manila",
    "timing_preference": "2 hours"
  }'
```

### Test Agent Proxy (SSE)
```bash
curl -N https://56esu4j6ukmbjfwzqoml7jsjvq0uwrdw.lambda-url.us-west-2.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the admission requirements?",
    "session_id": "test-123",
    "phone_number": "+15551234567",
    "student_name": "Test Student"
  }'
```

## Notes

- All resources are deployed in **us-west-2** region
- Knowledge Base is managed via Console (not CDK) to avoid permission complexity
- OpenSearch collection was automatically created by Bedrock during KB setup
- Memory is managed by Strands SDK, no manual creation needed
- CDK stack has RETAIN policy on S3 bucket to preserve documents
