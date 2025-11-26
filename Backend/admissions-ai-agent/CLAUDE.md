# Backend Infrastructure - AWS CDK and Lambda Functions

## Overview

This directory contains all backend infrastructure defined as code using AWS CDK (TypeScript), including Lambda functions, API Gateway, DynamoDB tables, SQS queues, and IAM roles.

## Directory Structure

```
Backend/admissions-ai-agent/
├── CLAUDE.md                          # This file
├── package.json                       # CDK dependencies (aws-cdk-lib, constructs)
├── tsconfig.json                      # TypeScript config with strict mode
├── cdk.json                           # CDK configuration
├── .env.example                       # Backend environment variables template
├── bin/
│   └── admissions-ai-agent.ts        # CDK app entry point
├── lib/
│   ├── admissions-agent-stack.ts     # Main infrastructure stack
│   └── amplify-hosting-stack.ts      # Optional frontend hosting
├── lambda/                            # See lambda/CLAUDE.md
├── layers/                            # Lambda layers for dependencies
├── AgentCore/                         # See AgentCore/CLAUDE.md
├── knowledge-base/                    # Knowledge base documents
└── deploy-scripts/                    # Deployment automation
```

## AWS Resources Created

### Storage & Databases
- **S3 Bucket**: Stores knowledge base documents with versioning enabled
  - Used by Bedrock Knowledge Base for vector search
  - Bucket policy allows Bedrock service access

- **DynamoDB Tables** (on-demand billing):
  - `WhatsappSessions`: Tracks user sessions and conversation history
    - Partition key: `phone_number` (string)
    - Attributes: `sessions` (list), `latest_session_id`, `web_app_last_connect_date`, `web_app_last_connect_time`
  - `WhatsAppMessageTracking`: Logs WhatsApp message delivery status
    - Partition key: `eum_msg_id` (string, UUID)
    - Attributes: `phone_number`, `message_text`, `twilio_message_id`, `status`, `timestamp`, `error_message`

### Messaging & Queueing
- **SQS Queue**: `twilio-whatsapp-queue` for asynchronous WhatsApp messaging
  - Visibility timeout: 300 seconds (5 minutes)
  - Message retention: 14 days
  - Dead-letter queue configured with max receive count: 3
  - Exponential backoff retry policy

### Compute
- **Lambda Functions**:
  - `agent-proxy`: Node.js 20 runtime, streaming response handler
    - Timeout: 30 seconds
    - Memory: 512 MB
    - Function URL with streaming enabled
  - `form-submission`: Python 3.12 runtime, Salesforce Lead creation
    - Timeout: 15 seconds
    - Memory: 256 MB
  - `whatsapp-sender`: Python 3.12 runtime, Twilio message sending
    - Timeout: 15 seconds
    - Memory: 256 MB
    - Triggered by SQS queue

- **Lambda Layers**:
  - `salesforce-layer`: Contains simple-salesforce, requests libraries
  - `twilio-layer`: Contains twilio, aiohttp libraries

### API & Networking
- **API Gateway**: REST API for form submission
  - POST endpoint: `/submit`
  - CORS enabled for frontend domain
  - Lambda proxy integration with form-submission function

### Container Registry
- **ECR Repository**: Stores AgentCore container images
  - Used by `agentcore launch` for agent deployment
  - Lifecycle policy: Keep last 5 images

### IAM Roles & Policies
- **AgentCore Execution Role**: Allows agent to access:
  - Bedrock (InvokeModel, Knowledge Base retrieval, Memory operations)
  - S3 (read knowledge base documents)
  - DynamoDB (read/write sessions and message tracking)
  - SQS (send messages to WhatsApp queue)
  - CloudWatch Logs (agent logging)

- **Lambda Execution Roles**: Scoped permissions for each Lambda function

## CDK Stack Development Guidelines

### Stack Definition Pattern

```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';

export class AdmissionsAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create resources with descriptive names
    // Export important ARNs and URLs as stack outputs
  }
}
```

### Resource Naming Convention
- Use descriptive names with project prefix: `admissions-agent-{resource-type}`
- Example: `admissions-agent-sessions-table`, `admissions-agent-kb-bucket`

### Environment Variables for Lambda Functions

All Lambda functions should receive environment variables via CDK:

```typescript
const lambdaFunction = new lambda.Function(this, 'MyFunction', {
  environment: {
    // Always include
    AWS_REGION: this.region,
    LOG_LEVEL: 'INFO',

    // Function-specific
    TABLE_NAME: table.tableName,
    QUEUE_URL: queue.queueUrl,
  }
});
```

### Stack Outputs

Always export critical resource identifiers:

```typescript
new cdk.CfnOutput(this, 'AgentProxyFunctionUrl', {
  value: agentProxyFunction.functionUrl?.url || '',
  description: 'Agent Proxy Lambda Function URL for SSE streaming',
});

new cdk.CfnOutput(this, 'FormSubmissionApiUrl', {
  value: api.url,
  description: 'API Gateway URL for form submission',
});

new cdk.CfnOutput(this, 'KnowledgeBaseBucketName', {
  value: kbBucket.bucketName,
  description: 'S3 bucket for knowledge base documents',
});

new cdk.CfnOutput(this, 'AgentExecutionRoleArn', {
  value: agentRole.roleArn,
  description: 'IAM role ARN for AgentCore execution',
});

new cdk.CfnOutput(this, 'EcrRepositoryUri', {
  value: ecrRepo.repositoryUri,
  description: 'ECR repository URI for AgentCore images',
});
```

## Data Models

### WhatsappSessions Table Schema

```typescript
{
  phone_number: string;              // Partition key, E.164 format
  sessions: string[];                // Array of session UUIDs
  latest_session_id: string;         // Most recent session UUID
  web_app_last_connect_date: string; // ISO date: "2025-01-15"
  web_app_last_connect_time: string; // Time: "14:30:00"
}
```

### WhatsAppMessageTracking Table Schema

```typescript
{
  eum_msg_id: string;                // Partition key, UUID
  phone_number: string;              // Recipient phone
  message_text: string;              // Message content
  twilio_message_id: string;         // Twilio SID
  status: string;                    // "sent" | "delivered" | "failed"
  timestamp: string;                 // ISO timestamp
  error_message?: string;            // Optional error details
}
```

### SQS Message Format

```typescript
{
  phone_number: string;              // E.164 format
  message: string;                   // Personalized message text
  timing_preference: string;         // "2 hours" | "business hours"
  student_name: string;              // FirstName LastName
  eum_msg_id: string;                // UUID for tracking
}
```

## Deployment Process

### Initial Deployment

1. **Install dependencies**:
   ```bash
   cd Backend/admissions-ai-agent
   npm install
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with AWS credentials and Salesforce/Twilio credentials
   ```

3. **Build Lambda layers**:
   ```bash
   cd layers/salesforce
   pip install -r requirements.txt -t python/lib/python3.12/site-packages/

   cd ../twilio
   pip install -r requirements.txt -t python/lib/python3.12/site-packages/
   ```

4. **Synthesize CDK stack**:
   ```bash
   cd ../../
   npx cdk synth
   ```

5. **Deploy stack**:
   ```bash
   npx cdk deploy
   ```

6. **Save outputs**: Copy stack outputs to `.env` file for agent and frontend configuration

### Updating Infrastructure

```bash
# After modifying stack code
npx cdk diff           # Preview changes
npx cdk deploy         # Apply changes
```

### Destroying Infrastructure

```bash
npx cdk destroy        # WARNING: Deletes all resources including data
```

## Lambda Layer Management

### Building Salesforce Layer

```bash
cd layers/salesforce
mkdir -p python/lib/python3.12/site-packages
pip install -r requirements.txt -t python/lib/python3.12/site-packages/
zip -r salesforce-layer.zip python/
```

**Dependencies** (`requirements.txt`):
```
simple-salesforce==1.12.4
requests==2.31.0
```

### Building Twilio Layer

```bash
cd layers/twilio
mkdir -p python/lib/python3.12/site-packages
pip install -r requirements.txt -t python/lib/python3.12/site-packages/
zip -r twilio-layer.zip python/
```

**Dependencies** (`requirements.txt`):
```
twilio==9.0.0
aiohttp==3.9.0
```

## IAM Permissions Reference

### AgentCore Execution Role Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:Retrieve",
        "bedrock:GetMemory",
        "bedrock:PutMemory",
        "bedrock:DeleteMemory"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::admissions-agent-kb-bucket",
        "arn:aws:s3:::admissions-agent-kb-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/WhatsappSessions",
        "arn:aws:dynamodb:*:*:table/WhatsAppMessageTracking"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:*:*:twilio-whatsapp-queue"
    }
  ]
}
```

## Monitoring & Observability

### CloudWatch Metrics to Track
- Lambda invocation count, duration, errors, throttles
- API Gateway request count, latency, 4xx/5xx errors
- DynamoDB read/write capacity, throttles
- SQS queue depth, message age, dead-letter queue depth

### CloudWatch Alarms to Create
- Lambda error rate > 5%
- API Gateway 5xx error rate > 1%
- SQS queue depth > 1000 messages
- DynamoDB throttling events
- Dead-letter queue receives messages

### CloudWatch Logs
All Lambda functions automatically log to CloudWatch Logs:
- Log group: `/aws/lambda/{function-name}`
- Retention: 7 days (configurable in CDK)

## Common Issues & Solutions

### Issue: CDK Deploy Fails with Permission Denied
**Solution**: Ensure AWS credentials are configured with sufficient permissions:
```bash
aws sts get-caller-identity  # Verify credentials
aws configure                # Set credentials if needed
```

### Issue: Lambda Function Timeout
**Solution**: Increase timeout in CDK stack definition:
```typescript
timeout: cdk.Duration.seconds(30)
```

### Issue: CORS Errors from Frontend
**Solution**: Ensure API Gateway CORS configuration includes frontend origin:
```typescript
defaultCorsPreflightOptions: {
  allowOrigins: ['https://your-frontend-domain.com'],
  allowMethods: ['POST', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
}
```

### Issue: Lambda Layer Not Found
**Solution**: Rebuild layer and redeploy:
```bash
cd layers/salesforce
rm -rf python/
mkdir -p python/lib/python3.12/site-packages
pip install -r requirements.txt -t python/lib/python3.12/site-packages/
```

## Security Best Practices

1. **Secrets Management**: Use AWS Secrets Manager for Salesforce/Twilio credentials (not environment variables)
2. **Least Privilege**: IAM roles should have minimal required permissions
3. **Encryption**: Enable encryption at rest for DynamoDB and S3
4. **VPC Configuration**: Consider deploying Lambdas in VPC for enhanced security
5. **API Gateway Auth**: Add AWS IAM authentication or API keys for production

## Cost Optimization

- **DynamoDB**: Use on-demand billing for unpredictable traffic
- **Lambda**: Right-size memory allocation (256MB default, increase only if needed)
- **S3**: Enable lifecycle policies to archive old knowledge base versions
- **CloudWatch Logs**: Set retention period to 7 days for non-critical logs

## Testing Infrastructure

```bash
# Validate CDK code
npx cdk synth

# Run CDK unit tests
npm test

# Integration tests (requires deployed stack)
pytest tests/integration/
```

## Related Documentation

- **Lambda Functions**: See `lambda/CLAUDE.md` for Lambda development guidelines
- **Agent Development**: See `AgentCore/CLAUDE.md` for agent and tools development
- **Data Models**: See `docs/kiro docs/design.md` for detailed data model specifications
- **Requirements**: See `docs/kiro docs/requirements.md` for infrastructure requirements
