# Agent Proxy Lambda

Proxies requests to Bedrock AgentCore and streams responses via Server-Sent Events (SSE).

## Overview

This Lambda function acts as a bridge between the frontend chat interface and the Bedrock-hosted AI agent. It handles:
- Request parsing and validation
- Session management
- SSE streaming of agent responses
- Error handling with user-friendly messages

## Properties Implemented

### Property 30: Agent Proxy streams responses via SSE
The Lambda uses `awslambda.streamifyResponse` to enable Server-Sent Events streaming. The frontend receives real-time responses as the agent generates them.

### Property 31: Agent responses streamed chunk-by-chunk
Agent responses are streamed incrementally, chunk-by-chunk, providing a responsive user experience with minimal latency.

## API

### Request

**Method:** POST
**Content-Type:** application/json

```json
{
  "prompt": "What are the admission requirements?",
  "session_id": "optional-session-id",
  "phone_number": "+15551234567",
  "student_name": "John Doe"
}
```

**Required Fields:**
- `prompt`: The user's message (string)

**Optional Fields:**
- `session_id` or `sessionId`: Session identifier for conversation continuity (generated if not provided)
- `phone_number` or `phoneNumber`: Student's phone number for logging
- `student_name` or `studentName`: Student's name for personalization

### Response

**Content-Type:** text/event-stream

The response is a stream of Server-Sent Events:

#### 1. Connection Event
```
event: connection
data: {"type":"connected","sessionId":"session-123","timestamp":"2024-01-15T10:30:00.000Z"}
```

#### 2. Chunk Events (multiple)
```
event: chunk
data: {"type":"chunk","text":"Hello! ","chunkNumber":1,"sessionId":"session-123"}

event: chunk
data: {"type":"chunk","text":"How can I","chunkNumber":2,"sessionId":"session-123"}

event: chunk
data: {"type":"chunk","text":" help you?","chunkNumber":3,"sessionId":"session-123"}
```

#### 3. Complete Event
```
event: complete
data: {"type":"complete","sessionId":"session-123","totalChunks":3,"fullResponse":"Hello! How can I help you?","timestamp":"2024-01-15T10:30:05.000Z"}
```

#### 4. Error Event (if error occurs)
```
event: error
data: {"type":"error","message":"We encountered an issue processing your request. Please try again.","timestamp":"2024-01-15T10:30:00.000Z"}
```

## Environment Variables

Required environment variables:
- `AGENT_ID`: Bedrock Agent ID
- `AGENT_ALIAS_ID`: Bedrock Agent Alias ID
- `AWS_REGION`: AWS region (defaults to us-east-1)

## Testing

The Lambda includes comprehensive unit tests covering:
- SSE streaming functionality
- Chunk-by-chunk response handling
- Session management
- Error handling
- CORS headers
- Request validation

### Run Tests

```bash
npm install
npm test
```

### Test Results

```
Test Suites: 1 passed, 1 total
Tests:       12 passed, 12 total
```

All tests passing! ✓

## Error Handling

The Lambda follows the project principle of never exposing technical details to users:

- **Input validation errors**: Returns specific error message (e.g., "Missing or invalid 'prompt' field")
- **Bedrock API errors**: Returns generic user-friendly message ("We encountered an issue processing your request. Please try again.")
- **Streaming errors**: Sends error event via SSE and gracefully terminates stream

All errors are logged to CloudWatch for debugging while keeping the user experience friendly.

## CORS

The Lambda includes CORS headers to allow cross-origin requests from the frontend:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Headers: Content-Type`
- `Access-Control-Allow-Methods: POST, OPTIONS`

## Deployment

This Lambda is deployed via AWS CDK as part of the main infrastructure stack. The CDK configuration includes:
- Node.js 20 runtime
- Lambda Function URL with streaming enabled
- IAM permissions for Bedrock Agent invocation
- Environment variables for Agent ID and Alias

## Dependencies

- `@aws-sdk/client-bedrock-agent-runtime`: AWS SDK for Bedrock Agent Runtime

## Integration

The frontend connects to this Lambda via its Function URL and consumes the SSE stream using the EventSource API or a custom SSE client.

See `Frontend/admissions-chat/CLAUDE.md` for frontend integration details.
