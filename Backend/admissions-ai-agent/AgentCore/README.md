# AI Admissions Agent Core

Bedrock-hosted AI agent using Strands SDK for university admissions assistance.

## Overview

The AgentCore is the brain of the admissions system. It's an AI agent powered by Claude Sonnet 4.5 via Amazon Bedrock, equipped with custom tools to:
- Query and update Salesforce CRM
- Send WhatsApp messages via SQS
- Search admissions knowledge base
- Guide prospective students through the admissions process

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  AgentCore                          │
│  (Strands SDK + Amazon Bedrock + Claude Sonnet 4.5) │
└──────────────┬──────────────────────────────────────┘
               │
       ┌───────┴───────┐
       │    Tools      │
       └───────┬───────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼───┐  ┌──▼────┐
│Salesforce│ │WhatsApp│ │Knowledge│
│   Tool   │ │  Tool  │ │  Tool   │
└──────────┘ └────────┘ └─────────┘
    │            │            │
┌───▼────┐  ┌───▼───┐   ┌───▼───┐
│Salesforce│ │  SQS  │   │   S3  │
│   CRM    │ │ Queue │   │  KB   │
└──────────┘ └───────┘   └───────┘
```

## Properties Implemented

### Property 10: Agent searches S3 knowledge base
The agent uses the `search_admissions_knowledge` tool to retrieve accurate information from the university's admissions documentation stored in S3.

### Property 11: Agent queries Salesforce for Lead status
The `query_salesforce_leads` tool allows the agent to look up student application status and details from Salesforce CRM.

### Property 12: Agent creates Salesforce Tasks
The `create_salesforce_task` tool creates follow-up tasks for human advisors when escalation is needed.

### Property 27: Agent schedules WhatsApp messages
The `send_whatsapp_message` tool queues messages via SQS for delivery according to student timing preferences.

## Project Structure

```
AgentCore/
├── agent.py                 # Main agent initialization and invocation
├── tools/                   # Custom tool implementations
│   ├── __init__.py
│   ├── salesforce_tool.py   # Salesforce CRM operations
│   ├── whatsapp_tool.py     # WhatsApp messaging via SQS
│   └── knowledge_tool.py    # Knowledge base search
├── tests/                   # Unit tests for tools
├── Dockerfile               # Container image for Bedrock deployment
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Tools

### 1. Salesforce Tool

**Functions:**
- `query_salesforce_leads(email, phone, last_name, limit)` - Search for student leads
- `create_salesforce_task(lead_email, subject, description, priority, due_date)` - Create follow-up tasks

**Usage:**
```python
# Query leads
result = query_salesforce_leads(email="student@example.com")

# Create task
result = create_salesforce_task(
    lead_email="student@example.com",
    subject="Follow up on program requirements",
    description="Student has questions about graduate program prerequisites"
)
```

### 2. WhatsApp Tool

**Functions:**
- `send_whatsapp_message(phone_number, message, timing_preference, student_name)` - Queue WhatsApp message

**Usage:**
```python
result = send_whatsapp_message(
    phone_number="+15551234567",
    message="Your advisor will contact you soon!",
    timing_preference="2 hours",
    student_name="John Doe"
)
```

**Timing Preferences:**
- "as soon as possible" - Immediate delivery
- "2 hours" - Deliver in 2 hours
- "4 hours" - Deliver in 4 hours
- "tomorrow morning" - Deliver next morning

### 3. Knowledge Base Tool

**Functions:**
- `search_admissions_knowledge(query, topic)` - Search admissions documentation

**Usage:**
```python
result = search_admissions_knowledge(
    query="undergraduate admission requirements",
    topic="requirements"
)
```

**Topics:**
- requirements
- programs
- deadlines
- financial
- campus
- general

## System Prompt

The agent is configured with a comprehensive system prompt that defines:
- Role as AI admissions advisor
- Capabilities (student management, communication, knowledge search)
- Guidelines (be helpful, provide accurate info, respect timing, escalate when needed)
- Example interactions

See `agent.py` for the full system prompt.

## Environment Variables

Required environment variables:

```bash
# Salesforce
SF_USERNAME=your_salesforce_username
SF_PASSWORD=your_salesforce_password
SF_TOKEN=your_salesforce_security_token

# AWS
AWS_REGION=us-east-1
WHATSAPP_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/account/queue-name
KNOWLEDGE_BASE_BUCKET=admissions-knowledge-base

# Model Config
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
MODEL_TEMPERATURE=0.7

# Logging
LOG_LEVEL=INFO
```

## Installation

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SF_USERNAME=your_username
export SF_PASSWORD=your_password
export SF_TOKEN=your_token
export AWS_REGION=us-east-1
export WHATSAPP_QUEUE_URL=your_queue_url
export KNOWLEDGE_BASE_BUCKET=your_bucket_name

# Run agent
python agent.py
```

### Docker Build

```bash
# Build image
docker build -t admissions-agent .

# Run container
docker run -e SF_USERNAME=... -e SF_PASSWORD=... admissions-agent
```

## Deployment to Bedrock

### 1. Build and Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t admissions-agent .
docker tag admissions-agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/admissions-agent:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/admissions-agent:latest
```

### 2. Deploy via CDK

The CDK stack (in `lib/admissions-agent-stack.ts`) handles:
- Creating ECR repository
- Defining ECS task with agent image
- Setting up IAM roles with Bedrock permissions
- Configuring environment variables from Secrets Manager

```bash
cd ../..
npm run cdk deploy
```

### 3. Register with Bedrock

After deployment, register the agent with Amazon Bedrock:

1. Go to Bedrock Console > Agents
2. Create new agent
3. Select Claude Sonnet 4.5 as foundation model
4. Point to deployed ECS task/Lambda
5. Configure action groups for tools
6. Create alias and deploy

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_salesforce_tool.py

# Run with coverage
pytest --cov=tools tests/
```

### Integration Tests

```bash
# Test with real Salesforce (requires credentials)
pytest tests/integration/ --integration

# Test with mocked AWS services
pytest tests/ --mock-aws
```

## Usage Example

```python
from agent import create_admissions_agent, invoke_agent

# Create agent
agent = create_admissions_agent(
    model_id="us.amazon.nova-pro-v1:0",
    temperature=0.7,
    enable_streaming=True
)

# Invoke with user prompt
response = invoke_agent(
    agent=agent,
    prompt="What are the admission requirements for graduate programs?",
    session_id="session-123",
    phone_number="+15551234567",
    student_name="John Doe"
)

print(response['message']['content'][0]['text'])
```

## Monitoring

### CloudWatch Logs

All agent invocations and tool calls are logged to CloudWatch:
- Agent requests and responses
- Tool invocations and results
- Errors and exceptions

### Bedrock Metrics

Monitor in Bedrock Console:
- Invocation count
- Token usage
- Latency
- Error rate

### Custom Metrics

The agent publishes custom metrics via CloudWatch:
- Tools used per conversation
- Escalation rate (tasks created)
- Knowledge base search success rate

## Error Handling

The agent follows a graceful degradation strategy:

1. **Tool Failures**: If a tool fails, the agent acknowledges the issue and offers alternatives
2. **Salesforce Unavailable**: Creates task for manual follow-up
3. **WhatsApp Queue Full**: Offers to create Salesforce task instead
4. **Knowledge Base Empty**: Directs to website or human advisor

All errors are logged but never expose technical details to users.

## Security

### IAM Roles

The agent requires permissions for:
- Bedrock model invocation
- S3 knowledge base access (read-only)
- SQS message sending
- CloudWatch logging

### Secrets Management

Salesforce credentials are stored in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name admissions-agent/salesforce \
  --secret-string '{"username":"...","password":"...","token":"..."}'
```

### Data Privacy

- Agent does not store conversation history
- Phone numbers and emails are logged but encrypted at rest
- PII is only accessed when necessary for the task

## Troubleshooting

### Agent not responding

Check CloudWatch logs for:
- Bedrock invocation errors
- Tool failures
- Model timeout

### Salesforce connection failures

Verify:
- SF credentials in Secrets Manager
- Security token is current
- IP allowlist includes Lambda/ECS IPs

### WhatsApp messages not sending

Check:
- SQS queue exists and is accessible
- WhatsApp Sender Lambda is running
- Queue URL environment variable is correct

### Knowledge base returns no results

Verify:
- S3 bucket exists and has content
- Agent has S3 read permissions
- File formats are .md or .txt

## Future Enhancements

1. **Bedrock Knowledge Base Integration**: Replace simple S3 search with Bedrock KB for vector search
2. **Memory Persistence**: Add Bedrock Memory for long-term conversation context
3. **Multi-turn Conversations**: Implement conversation state management
4. **A/B Testing**: Test different system prompts and tool configurations
5. **Agent Evaluation**: Add automated testing for agent responses

## Support

For issues or questions:
- Check CloudWatch logs first
- Review this README and CLAUDE.md in this directory
- Contact the development team

## License

Internal use only - University Admissions System
