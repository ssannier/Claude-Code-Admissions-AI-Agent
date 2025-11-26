# Lambda Functions Development Guidelines

## Overview

This directory contains three Lambda functions that handle backend workflows:
1. **agent-proxy**: Streams AI responses from Bedrock AgentCore to frontend via SSE
2. **form-submission**: Creates Salesforce Leads from inquiry form submissions
3. **whatsapp-sender**: Sends WhatsApp messages via Twilio from SQS queue

## Directory Structure

```
lambda/
├── CLAUDE.md                          # This file
├── agent-proxy/                       # Node.js 20 streaming proxy
│   ├── index.js                       # Main handler with streamifyResponse
│   ├── package.json                   # Dependencies: @aws-sdk/client-bedrock-agent-runtime
│   └── __tests__/
│       └── index.test.js              # Unit tests
├── form-submission/                   # Python 3.12 Salesforce integration
│   ├── form_submission.py             # Main handler
│   ├── requirements.txt               # Uses salesforce Lambda layer
│   └── tests/
│       ├── test_form_submission.py    # Unit tests
│       └── test_properties.py         # Property-based tests
└── whatsapp-sender/                   # Python 3.12 Twilio integration
    ├── send_whatsapp_twilio.py        # Main handler
    ├── requirements.txt               # Uses twilio Lambda layer
    └── tests/
        ├── test_whatsapp_sender.py    # Unit tests
        └── test_properties.py         # Property-based tests
```

## 1. Agent Proxy Lambda (Node.js)

### Purpose
Stream responses from Bedrock AgentCore to frontend using Server-Sent Events (SSE).

### Handler Signature

```javascript
const { BedrockAgentRuntimeClient, InvokeAgentCommand } = require('@aws-sdk/client-bedrock-agent-runtime');
const awslambda = require('aws-lambda');

exports.handler = awslambda.streamifyResponse(async (event, responseStream, context) => {
  // Parse request body
  const { prompt, session_id, phone_number, system_message } = JSON.parse(event.body);

  // Invoke AgentCore with streaming
  const client = new BedrockAgentRuntimeClient({ region: process.env.AWS_REGION });
  const command = new InvokeAgentCommand({
    agentId: process.env.AGENT_ID,
    agentAliasId: process.env.AGENT_ALIAS_ID,
    sessionId: session_id,
    inputText: prompt,
    enableTrace: false,
    streamingConfigurations: {
      streamFinalResponse: true
    }
  });

  // Stream chunks as SSE events
  try {
    const response = await client.send(command);
    for await (const chunk of response.completion) {
      if (chunk.chunk?.bytes) {
        const text = new TextDecoder().decode(chunk.chunk.bytes);
        const event = JSON.parse(text);

        // Forward as SSE event
        responseStream.write(`data: ${JSON.stringify(event)}\n\n`);
      }
    }
    responseStream.end();
  } catch (error) {
    console.error('AgentCore invocation error:', error);
    responseStream.write(`data: ${JSON.stringify({ error: 'Agent unavailable' })}\n\n`);
    responseStream.end();
  }
});
```

### Environment Variables

```javascript
{
  AGENT_RUNTIME_ARN: string;    // Bedrock AgentCore runtime ARN
  AWS_REGION: string;            // AWS region
  LOG_LEVEL: string;             // 'INFO' | 'DEBUG' | 'ERROR'
}
```

### SSE Event Format

All events must follow SSE format: `data: {json}\n\n`

**Event Types**:
```javascript
// Streaming text chunk
{ response: "text content" }

// Tool usage indicator
{ thinking: "🔍 Searching knowledge base" }

// Tool result
{ tool_result: "Found 3 relevant documents" }

// Final complete response
{ final_result: "complete response text" }

// Error
{ error: "User-friendly error message" }
```

### Error Handling

**Never expose technical details to users**:
```javascript
// ❌ BAD
responseStream.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);

// ✅ GOOD
console.error('AgentCore error:', error); // Log technical details
responseStream.write(`data: ${JSON.stringify({
  error: 'Our AI assistant is temporarily unavailable. Please try again.'
})}\n\n`);
```

### Testing

```javascript
// __tests__/index.test.js
const { handler } = require('../index');

describe('Agent Proxy Lambda', () => {
  it('should stream SSE events', async () => {
    const event = {
      body: JSON.stringify({
        prompt: 'Hello',
        session_id: 'test-session',
        phone_number: '+15551234567'
      })
    };

    const chunks = [];
    const responseStream = {
      write: (chunk) => chunks.push(chunk),
      end: () => {}
    };

    await handler(event, responseStream, {});

    expect(chunks.length).toBeGreaterThan(0);
    expect(chunks[0]).toMatch(/^data: /);
  });
});
```

### Property-Based Testing

**Property 36: Chunks forwarded as SSE events**
```javascript
// Every chunk received from AgentCore should be forwarded as SSE event with "data:" prefix
```

**Property 44: Proxy errors send error events**
```javascript
// Any error should send error event to frontend, not throw exception
```

---

## 2. Form Submission Lambda (Python)

### Purpose
Create Salesforce Lead records from inquiry form submissions.

### Handler Signature

```python
import json
import os
from simple_salesforce import Salesforce
import logging

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

def lambda_handler(event, context):
    """
    Handle form submission from API Gateway.

    Input: API Gateway event with form data in body
    Output: {statusCode: 200, body: {success: true, message: "..."}}
    """
    try:
        # Parse form data
        body = json.loads(event['body'])
        first_name = body['firstName']
        last_name = body['lastName']
        email = body['email']
        cell_phone = body['cellPhone']
        home_phone = body.get('homePhone', '')
        headquarters = body['headquarters']
        program_type = body['programType']

        # Validate required fields
        if not all([first_name, last_name, email, cell_phone, headquarters, program_type]):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'message': 'All required fields must be provided.'
                })
            }

        # Connect to Salesforce
        sf = Salesforce(
            username=os.environ['SF_USERNAME'],
            password=os.environ['SF_PASSWORD'],
            security_token=os.environ['SF_TOKEN']
        )

        # Create Lead
        lead_data = {
            'FirstName': first_name,
            'LastName': last_name,
            'Email': email,
            'Phone': cell_phone,
            'Description': f"Headquarters: {headquarters}\nProgram Type: {program_type}",
            'Company': 'Not Provided',
            'LeadSource': 'Web Form - Admissions',
            'Status': 'New'
        }

        result = sf.Lead.create(lead_data)

        logger.info(f"Created Lead: {result['id']}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Configure for your domain
            },
            'body': json.dumps({
                'success': True,
                'message': 'Your inquiry has been submitted successfully.',
                'leadId': result['id']
            })
        }

    except Exception as e:
        logger.error(f"Error creating Lead: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'message': 'We encountered an error processing your request. Please try again.'
            })
        }
```

### Environment Variables

```python
{
    'SF_USERNAME': str,      # Salesforce username
    'SF_PASSWORD': str,      # Salesforce password
    'SF_TOKEN': str,         # Salesforce security token
    'AWS_REGION': str,       # AWS region
    'LOG_LEVEL': str         # 'INFO' | 'DEBUG' | 'ERROR'
}
```

### Salesforce Lead Schema

```python
{
    'FirstName': str,
    'LastName': str,
    'Email': str,
    'Phone': str,              # Cell phone from form
    'Description': str,        # Contains headquarters and program type
    'Company': 'Not Provided', # Required field, static value
    'LeadSource': 'Web Form - Admissions',
    'Status': 'New'            # Will be updated to "Working" during handoff
}
```

### Testing

```python
# tests/test_form_submission.py
import json
import pytest
from unittest.mock import patch, MagicMock
from form_submission import lambda_handler

def test_successful_lead_creation():
    event = {
        'body': json.dumps({
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john@example.com',
            'cellPhone': '+15551234567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        })
    }

    with patch('form_submission.Salesforce') as mock_sf:
        mock_sf.return_value.Lead.create.return_value = {'id': 'test-lead-id'}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'leadId' in body

def test_missing_required_field():
    event = {
        'body': json.dumps({
            'firstName': 'John',
            # Missing lastName
            'email': 'john@example.com'
        })
    }

    response = lambda_handler(event, None)
    assert response['statusCode'] == 400
```

### Property-Based Testing

```python
# tests/test_properties.py
from hypothesis import given, strategies as st
import json

# Feature: ai-admissions-agent, Property 1: Form validation rejects empty required fields
@given(
    first_name=st.one_of(st.none(), st.just('')),
    last_name=st.text(),
    email=st.emails()
)
def test_form_validation_rejects_empty_fields(first_name, last_name, email):
    """Any form submission with empty required fields should be rejected."""
    event = {
        'body': json.dumps({
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'cellPhone': '+15551234567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        })
    }

    response = lambda_handler(event, None)

    if not first_name:
        assert response['statusCode'] == 400
    # else: should succeed

# Feature: ai-admissions-agent, Property 2: Valid form submission creates Salesforce Lead
@given(
    first_name=st.text(min_size=1),
    last_name=st.text(min_size=1)
)
def test_valid_form_creates_lead(first_name, last_name):
    """Valid form data should create a Lead with correct LeadSource and Status."""
    # Test implementation
    pass
```

---

## 3. WhatsApp Sender Lambda (Python)

### Purpose
Send WhatsApp messages via Twilio from SQS queue and log delivery status.

### Handler Signature

```python
import json
import os
import boto3
from twilio.rest import Client
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

dynamodb = boto3.resource('dynamodb')
tracking_table = dynamodb.Table(os.environ['MESSAGE_TRACKING_TABLE'])

def lambda_handler(event, context):
    """
    Process SQS messages and send WhatsApp via Twilio.

    Input: SQS event with Records containing message data
    Output: None (logs to CloudWatch and DynamoDB)
    """
    # Initialize Twilio client
    twilio_client = Client(
        os.environ['TWILIO_ACCOUNT_SID'],
        os.environ['TWILIO_AUTH_TOKEN']
    )
    twilio_phone = os.environ['TWILIO_PHONE_NUMBER']

    for record in event['Records']:
        try:
            # Parse SQS message
            message_body = json.loads(record['body'])
            phone_number = message_body['phone_number']
            message_text = message_body['message']
            timing_preference = message_body['timing_preference']
            student_name = message_body['student_name']
            eum_msg_id = message_body['eum_msg_id']

            logger.info(f"Sending WhatsApp to {phone_number}, tracking ID: {eum_msg_id}")

            # Send WhatsApp message via Twilio
            twilio_message = twilio_client.messages.create(
                from_=f'whatsapp:{twilio_phone}',
                to=f'whatsapp:{phone_number}',
                body=message_text
            )

            # Log delivery status to DynamoDB
            tracking_table.put_item(
                Item={
                    'eum_msg_id': eum_msg_id,
                    'phone_number': phone_number,
                    'message_text': message_text,
                    'twilio_message_id': twilio_message.sid,
                    'status': twilio_message.status,
                    'timestamp': datetime.utcnow().isoformat(),
                    'timing_preference': timing_preference,
                    'student_name': student_name
                }
            )

            logger.info(f"WhatsApp sent successfully: {twilio_message.sid}")

        except Exception as e:
            logger.error(f"Error sending WhatsApp: {str(e)}", exc_info=True)

            # Log error to tracking table
            try:
                tracking_table.put_item(
                    Item={
                        'eum_msg_id': message_body.get('eum_msg_id', 'unknown'),
                        'phone_number': message_body.get('phone_number', 'unknown'),
                        'message_text': message_body.get('message', ''),
                        'twilio_message_id': 'N/A',
                        'status': 'failed',
                        'timestamp': datetime.utcnow().isoformat(),
                        'error_message': str(e)
                    }
                )
            except:
                pass  # Best effort logging

            # Re-raise to trigger SQS retry
            raise
```

### Environment Variables

```python
{
    'TWILIO_ACCOUNT_SID': str,      # Twilio account SID
    'TWILIO_AUTH_TOKEN': str,       # Twilio auth token
    'TWILIO_PHONE_NUMBER': str,     # Twilio WhatsApp-enabled phone number
    'MESSAGE_TRACKING_TABLE': str,  # DynamoDB table name
    'AWS_REGION': str,
    'LOG_LEVEL': str
}
```

### SQS Message Format

```python
{
    'phone_number': str,         # E.164 format: "+15551234567"
    'message': str,              # Personalized message text
    'timing_preference': str,    # "2 hours" | "business hours"
    'student_name': str,         # "FirstName LastName"
    'eum_msg_id': str           # UUID for tracking
}
```

### Testing

```python
# tests/test_whatsapp_sender.py
import json
import pytest
from unittest.mock import patch, MagicMock
from send_whatsapp_twilio import lambda_handler

def test_successful_whatsapp_send():
    event = {
        'Records': [{
            'body': json.dumps({
                'phone_number': '+15551234567',
                'message': 'Test message',
                'timing_preference': '2 hours',
                'student_name': 'John Doe',
                'eum_msg_id': 'test-uuid'
            })
        }]
    }

    with patch('send_whatsapp_twilio.Client') as mock_client:
        mock_message = MagicMock()
        mock_message.sid = 'test-sid'
        mock_message.status = 'sent'
        mock_client.return_value.messages.create.return_value = mock_message

        with patch('send_whatsapp_twilio.tracking_table') as mock_table:
            lambda_handler(event, None)

            # Verify Twilio was called
            mock_client.return_value.messages.create.assert_called_once()

            # Verify DynamoDB was updated
            mock_table.put_item.assert_called_once()

def test_twilio_error_handling():
    # Test error logging and retry behavior
    pass
```

### Property-Based Testing

```python
# Feature: ai-admissions-agent, Property 28: WhatsApp Lambda sends via Twilio
# Feature: ai-admissions-agent, Property 29: Sent messages logged to tracking table

@given(
    phone=st.text(min_size=10),
    message=st.text(min_size=1)
)
def test_whatsapp_sends_and_logs(phone, message):
    """Every SQS message should result in Twilio send and DynamoDB log entry."""
    # Test implementation
    pass
```

---

## General Lambda Development Guidelines

### Error Handling Best Practices

1. **Log Technical Details, Show User-Friendly Messages**
```python
try:
    result = external_api_call()
except Exception as e:
    logger.error(f"API call failed: {str(e)}", exc_info=True)  # Technical details
    return {
        'statusCode': 500,
        'body': json.dumps({
            'message': 'We encountered a temporary issue. Please try again.'  # User-friendly
        })
    }
```

2. **Structured Logging**
```python
logger.info('Processing request', extra={
    'session_id': session_id,
    'phone_number': phone_number,
    'request_id': context.aws_request_id
})
```

3. **Always Return Proper Status Codes**
- 200: Success
- 400: Client error (validation failure)
- 500: Server error (unexpected exception)

### Testing Strategy

1. **Unit Tests**: Test individual functions with mocked dependencies
2. **Integration Tests**: Test Lambda with real AWS services (DynamoDB, SQS)
3. **Property-Based Tests**: Use Hypothesis (Python) or fast-check (JavaScript) for invariants

### Performance Optimization

1. **Connection Reuse**: Initialize clients outside handler for connection pooling
```python
# ✅ GOOD - Initialize once
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    table.put_item(...)  # Reuses connection

# ❌ BAD - Initialize every invocation
def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
```

2. **Async Operations**: Use async/await for I/O operations where possible

3. **Right-Size Memory**: Monitor CloudWatch metrics and adjust Lambda memory allocation

### Security Best Practices

1. **Never log sensitive data**: Passwords, tokens, API keys, credit cards
2. **Use Secrets Manager**: For Salesforce/Twilio credentials (not env vars in production)
3. **Validate Input**: Always validate and sanitize user input
4. **Principle of Least Privilege**: IAM roles should have minimal permissions

### Deployment Checklist

- [ ] Unit tests passing
- [ ] Property tests passing (100+ iterations)
- [ ] Environment variables configured
- [ ] Lambda layers attached
- [ ] IAM role permissions verified
- [ ] Timeout and memory settings appropriate
- [ ] CloudWatch alarms configured
- [ ] Error handling tested

## Related Documentation

- **Infrastructure**: See `../CLAUDE.md` for CDK stack and resource definitions
- **Agent Development**: See `../AgentCore/CLAUDE.md` for agent integration
- **Requirements**: See `docs/kiro docs/requirements.md` for detailed acceptance criteria
- **Data Models**: See `docs/kiro docs/design.md` for API contracts and schemas
