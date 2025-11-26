# Design Document

## Overview

The AI-Powered University Admissions Agent is a full-stack conversational AI platform built on AWS cloud services. The system consists of three main layers:

1. **Frontend Layer**: A Next.js 15 web application providing a modern landing page with inquiry form and real-time chat interface
2. **Backend Layer**: AWS infrastructure including Lambda functions, API Gateway, DynamoDB, and SQS for orchestrating workflows
3. **AI Agent Layer**: Bedrock AgentCore running a Strands-based conversational agent with Claude Sonnet 4.5

The platform enables prospective students to engage in natural conversations about university programs while automatically capturing leads in Salesforce CRM and facilitating handoffs to human enrollment advisors through WhatsApp messaging.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────────────┐         ┌──────────────────────────────┐ │
│  │  Landing Page    │         │    Chat Interface            │ │
│  │  + Inquiry Form  │────────▶│    (SSE Streaming)           │ │
│  └──────────────────┘         └──────────────────────────────┘ │
└─────────────┬───────────────────────────────┬──────────────────┘
              │                               │
              │ HTTPS                         │ SSE
              ▼                               ▼
┌─────────────────────────┐    ┌──────────────────────────────────┐
│   API Gateway           │    │   Agent Proxy Lambda             │
│   (Form Submission)     │    │   (Streaming Responses)          │
└────────────┬────────────┘    └────────────┬─────────────────────┘
             │                              │
             │                              │ Invoke
             ▼                              ▼
┌─────────────────────────┐    ┌──────────────────────────────────┐
│  Form Submission Lambda │    │   Bedrock AgentCore              │
│  (Create Salesforce     │    │   (Strands Agent + Claude 4.5)   │
│   Lead)                 │    │                                  │
└─────────────────────────┘    └────────────┬─────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
         ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
         │  Knowledge Base  │   │  Bedrock Memory  │   │  DynamoDB        │
         │  (Vector Search) │   │  (Conversation   │   │  (Sessions)      │
         │                  │   │   History)       │   │                  │
         └──────────────────┘   └──────────────────┘   └──────────────────┘
                                            │
                                            │ Advisor Handoff Tool
                                            ▼
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
         ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
         │  Salesforce CRM  │   │  SQS Queue       │   │  WhatsApp Lambda │
         │  (Leads, Tasks)  │   │  (Messages)      │───▶│  (Twilio API)    │
         └──────────────────┘   └──────────────────┘   └──────────────────┘
```

### Component Interaction Flow

**User Journey Flow:**

1. Student visits landing page → fills inquiry form → submits
2. Form Submission Lambda creates Salesforce Lead
3. Chat interface opens with system message containing form context
4. Student sends message → Agent Proxy Lambda → AgentCore
5. AgentCore retrieves conversation history from Memory
6. Agent processes message, may call tools (Knowledge Base search)
7. Agent streams response back through Agent Proxy to frontend
8. Agent stores messages in Memory
9. After engagement, agent offers advisor connection
10. Student consents → Agent executes advisor handoff tool
11. Handoff tool: searches Salesforce, updates Lead, creates Task, queues WhatsApp
12. WhatsApp Lambda sends message via Twilio

### Technology Stack

**Frontend:**
- Next.js 15 (App Router)
- React 19
- TypeScript 5
- Tailwind CSS 4
- Radix UI components
- react-markdown with syntax highlighting

**Backend Infrastructure:**
- AWS CDK 2.x (TypeScript)
- Lambda (Node.js 20 for proxy, Python 3.12 for others)
- API Gateway (REST API)
- DynamoDB (on-demand)
- SQS (standard queue)
- S3 (knowledge base storage)
- ECR (container registry)

**AI Agent:**
- AWS Bedrock AgentCore
- Strands Agent SDK
- Claude Sonnet 4.5 (global.anthropic.claude-sonnet-4-5-20250929-v1:0)
- Bedrock Knowledge Base with Titan Embeddings
- Bedrock Memory (short-term)

**External Integrations:**
- Salesforce CRM (simple-salesforce library)
- Twilio WhatsApp API

## Components and Interfaces

### Frontend Components

#### 1. Landing Page (`app/page.tsx`)
- **Purpose**: Entry point for prospective students
- **Responsibilities**:
  - Display hero section with university branding
  - Render inquiry form
  - Handle form submission
  - Open chat interface on successful submission
- **State**: Form data, chat open state, form context
- **Interface**: Renders `MapuaLandingPage` and `NemoChatInterface` components

#### 2. Inquiry Form (`components/inquiry-form.tsx`)
- **Purpose**: Capture student contact information and interests
- **Responsibilities**:
  - Validate form inputs (required fields, email format, phone format)
  - Submit form data to API Gateway
  - Pass form context to chat interface
- **State**: Form fields (firstName, lastName, email, cellPhone, homePhone, headquarters, programType)
- **Interface**:
  ```typescript
  interface FormData {
    firstName: string;
    lastName: string;
    email: string;
    cellPhone: string;
    homePhone?: string;
    headquarters: string;
    programType: string;
  }
  
  function submitInquiryForm(data: FormData): Promise<{success: boolean, message: string}>
  ```

#### 3. Chat Interface (`components/nemo/nemo-chat-interface.tsx`)
- **Purpose**: Real-time conversational UI with streaming responses
- **Responsibilities**:
  - Manage message state (user messages, AI messages, streaming message)
  - Handle SSE streaming from agent proxy
  - Display tool usage indicators
  - Auto-scroll to bottom
  - Provide message regeneration
- **State**: 
  - `messages: Message[]`
  - `currentStreamingMessage: string`
  - `isStreaming: boolean`
  - `currentTool: ToolStatus | null`
  - `sessionId: string`
- **Interface**:
  ```typescript
  interface Message {
    id: string;
    type: "user" | "ai";
    content: string;
    timestamp: number;
    toolStatus?: ToolStatus;
  }
  
  interface ToolStatus {
    icon: string;
    message: string;
    state: "running" | "completed";
  }
  ```

#### 4. Agent Client (`lib/agent-client.ts`)
- **Purpose**: Handle SSE streaming communication with agent proxy
- **Responsibilities**:
  - Establish SSE connection
  - Parse SSE events
  - Normalize event formats
  - Handle connection errors
- **Interface**:
  ```typescript
  async function* streamChatResponse(params: {
    message: string;
    sessionId: string;
    phoneNumber: string;
  }): AsyncGenerator<AgentStreamEvent>
  
  type AgentStreamEvent = 
    | { type: "response"; content: string }
    | { type: "tool_status"; icon: string; message: string }
    | { type: "tool_result"; content: string }
    | { type: "final"; content: string }
    | { type: "error"; message: string }
  ```

### Backend Components

#### 5. Form Submission Lambda (`lambda/form_submission.py`)
- **Purpose**: Create Salesforce leads from inquiry form submissions
- **Responsibilities**:
  - Parse API Gateway event
  - Validate form data
  - Connect to Salesforce
  - Create Lead record
  - Return success/error response
- **Environment Variables**: SF_USERNAME, SF_PASSWORD, SF_TOKEN
- **Interface**:
  ```python
  def lambda_handler(event, context):
      # Input: API Gateway event with form data in body
      # Output: {statusCode: 200, body: {success: true, message: "..."}}
  ```

#### 6. Agent Proxy Lambda (`lambda/agent-proxy/index.js`)
- **Purpose**: Stream responses from AgentCore to frontend
- **Responsibilities**:
  - Receive chat request from frontend
  - Invoke AgentCore with streaming
  - Forward chunks as SSE events
  - Handle errors gracefully
- **Environment Variables**: AGENT_RUNTIME_ARN, AWS_REGION
- **Interface**:
  ```javascript
  exports.handler = awslambda.streamifyResponse(async (event, responseStream) => {
      // Input: {prompt, session_id, phone_number}
      // Output: SSE stream of chunks
  })
  ```

#### 7. WhatsApp Sender Lambda (`lambda/send_whatsapp_twilio.py`)
- **Purpose**: Send WhatsApp messages via Twilio from SQS queue
- **Responsibilities**:
  - Consume messages from SQS
  - Send via Twilio API
  - Log delivery status to DynamoDB
  - Handle errors and retries
- **Environment Variables**: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, MESSAGE_TRACKING_TABLE
- **Interface**:
  ```python
  def lambda_handler(event, context):
      # Input: SQS event with Records containing message data
      # Output: None (logs to CloudWatch and DynamoDB)
  ```

### AI Agent Components

#### 8. Main Agent (`AgentCore/nemo_agent.py`)
- **Purpose**: Conversational AI agent orchestrating the student interaction
- **Responsibilities**:
  - Process incoming messages with conversation history
  - Stream responses with tool usage
  - Track sessions in DynamoDB
  - Store messages in Bedrock Memory
  - Provide context to tools
- **Environment Variables**: AWS_REGION, AGENTCORE_MEMORY_ID, SESSIONS_TABLE_NAME, UNIVERSITY_NAME, UNIVERSITY_SHORT_NAME, MAX_HISTORY_TURNS
- **Interface**:
  ```python
  @app.entrypoint
  async def strands_agent_bedrock(payload):
      # Input: {prompt, session_id, phone_number, system_message?}
      # Output: Async generator yielding event dicts
  ```

#### 9. Knowledge Base Retrieval Tool (`tools/retrieve_tool.py`)
- **Purpose**: Search university information using vector similarity
- **Responsibilities**:
  - Query Bedrock Knowledge Base
  - Filter by relevance score threshold (0.5)
  - Extract source attribution
  - Format results for agent
- **Environment Variables**: ENGLISH_KNOWLEDGE_BASE_ID, AWS_REGION
- **Interface**:
  ```python
  @tool
  def retrieve_university_info(text: str, numberOfResults: int = 5, score: float = 0.5) -> str:
      """Search the knowledge base for university information"""
  ```

#### 10. Advisor Handoff Tool (`tools/advisor_handoff_tool.py`)
- **Purpose**: Orchestrate complete handoff workflow
- **Responsibilities**:
  - Retrieve full conversation history from Memory
  - Search Salesforce for Lead by phone
  - Update Lead status to "Working"
  - Create Task with summary and transcript
  - Queue WhatsApp message to SQS
- **Environment Variables**: SF_USERNAME, SF_PASSWORD, SF_TOKEN, TWILIO_WHATSAPP_QUEUE_URL, AGENTCORE_MEMORY_ID
- **Interface**:
  ```python
  @tool
  def complete_advisor_handoff(
      conversation_summary: str,
      whatsapp_message: str,
      programs: str,
      concerns: str
  ) -> str:
      """Complete the advisor handoff workflow"""
  ```

#### 11. Session Utilities (`tools/session_utils.py`)
- **Purpose**: Manage session tracking and conversation history
- **Responsibilities**:
  - Sanitize phone numbers for actor_id
  - Fetch conversation history from Memory
  - Format history for agent context
- **Interface**:
  ```python
  def sanitize_phone_for_actor_id(phone: str) -> str:
      """Remove +, -, and spaces from phone number"""
  
  def fetch_conversation_history(
      session_id: str,
      phone_number: str,
      memory_id: str,
      max_turns: int
  ) -> str:
      """Retrieve last N turns from Bedrock Memory"""
  ```

### Infrastructure Components

#### 12. CDK Stack (`lib/admissions-agent-stack.ts`)
- **Purpose**: Define all AWS infrastructure as code
- **Responsibilities**:
  - Create S3 bucket for knowledge base
  - Create DynamoDB tables (WhatsappSessions, WhatsAppMessageTracking)
  - Create SQS queue with DLQ
  - Create Lambda functions with layers
  - Create API Gateway
  - Create IAM roles and policies
  - Create ECR repository
  - Output resource identifiers
- **Interface**: CDK constructs defining AWS resources

## Data Models

### Frontend Data Models

```typescript
// Message in chat interface
interface Message {
  id: string;                    // UUID
  type: "user" | "ai";           // Message sender
  content: string;               // Message text (markdown for AI)
  timestamp: number;             // Unix timestamp
  toolStatus?: ToolStatus;       // Optional tool usage indicator
}

// Tool usage indicator
interface ToolStatus {
  icon: string;                  // Emoji icon (🔍, 🤝)
  message: string;               // Status message
  state: "running" | "completed"; // Tool execution state
}

// Form submission data
interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  cellPhone: string;
  homePhone?: string;            // Optional
  headquarters: string;          // Campus location
  programType: string;           // undergraduate, graduate, etc.
}

// Agent stream events
type AgentStreamEvent = 
  | { type: "response"; content: string }
  | { type: "tool_status"; icon: string; message: string }
  | { type: "tool_result"; content: string }
  | { type: "final"; content: string }
  | { type: "error"; message: string }
```

### Backend Data Models

```python
# DynamoDB WhatsappSessions table
{
  "phone_number": str,           # Partition key (e.g., "+15551234567")
  "sessions": List[str],         # Array of session UUIDs
  "latest_session_id": str,      # Most recent session UUID
  "web_app_last_connect_date": str,  # ISO date (e.g., "2025-01-15")
  "web_app_last_connect_time": str   # Time (e.g., "14:30:00")
}

# DynamoDB WhatsAppMessageTracking table
{
  "eum_msg_id": str,             # Partition key (UUID)
  "phone_number": str,           # Recipient phone
  "message_text": str,           # Message content
  "twilio_message_id": str,      # Twilio SID
  "status": str,                 # "sent", "delivered", "failed"
  "timestamp": str,              # ISO timestamp
  "error_message": str           # Optional error details
}

# SQS WhatsApp message format
{
  "phone_number": str,
  "message": str,
  "timing_preference": str,      # "2 hours" or "business hours"
  "student_name": str,
  "eum_msg_id": str              # UUID for tracking
}

# Salesforce Lead object
{
  "FirstName": str,
  "LastName": str,
  "Email": str,
  "Phone": str,
  "Description": str,            # Contains headquarters and program type
  "Company": str,                # "Not Provided"
  "LeadSource": str,             # "Web Form - Admissions"
  "Status": str                  # "New" → "Working"
}

# Salesforce Task object
{
  "Subject": str,                # "Chat Conversation - [Name]"
  "Description": str,            # Summary + programs + concerns + transcript
  "WhoId": str,                  # Lead ID
  "Status": str,                 # "Not Started"
  "Priority": str,               # "Normal"
  "ActivityDate": str            # Today's date
}
```

### Agent Data Models

```python
# Agent payload (input)
{
  "prompt": str,                 # User message
  "session_id": str,             # UUID
  "phone_number": str,           # E.164 format
  "system_message": str          # Optional form context
}

# Agent event (output)
{
  "response": str                # Streaming text chunk
}
# OR
{
  "thinking": str                # Tool usage indicator
}
# OR
{
  "tool_result": str             # Tool execution result
}
# OR
{
  "final_result": str            # Complete response
}
# OR
{
  "error": str                   # Error message
}

# Bedrock Memory event
{
  "memory_id": str,
  "actor_id": str,               # Sanitized phone number
  "session_id": str,
  "messages": List[Tuple[str, str]]  # [(content, role)]
}

# Knowledge Base retrieval result
{
  "content": str,                # Document text
  "score": float,                # Relevance score (0-1)
  "location": {
    "s3Location": {
      "uri": str                 # S3 URI
    }
  },
  "metadata": {
    "x-amz-bedrock-kb-source-uri": str  # Document URL
  }
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Form validation rejects empty required fields
*For any* form submission, if any required field (firstName, lastName, email, cellPhone, headquarters, programType) is empty, the validation should reject the submission.
**Validates: Requirements 1.3**

### Property 2: Valid form submission creates Salesforce Lead
*For any* valid form data, submitting the form should create a Lead in Salesforce with LeadSource "Web Form - Admissions" and Status "New".
**Validates: Requirements 1.4**

### Property 3: Successful Lead creation opens chat with context
*For any* successful Salesforce Lead creation, the system should open the chat interface with a system message containing the form context.
**Validates: Requirements 1.5**

### Property 4: User messages display with correct styling
*For any* user message sent in the chat, the message should be displayed in a user-styled bubble with a timestamp.
**Validates: Requirements 2.2**

### Property 5: AI responses stream incrementally
*For any* AI response, the content should be delivered incrementally (streaming) rather than all at once.
**Validates: Requirements 2.3**

### Property 6: Completed AI messages include regenerate button
*For any* completed AI message, the message should be displayed in an AI-styled bubble with a regenerate button.
**Validates: Requirements 2.4**

### Property 7: Regenerate button triggers new response
*For any* AI message with a regenerate button, clicking the button should trigger generation of a new response.
**Validates: Requirements 2.5**

### Property 8: Factual questions trigger knowledge base search
*For any* factual question about university information, the system should call the knowledge base retrieval tool.
**Validates: Requirements 3.1**

### Property 9: Knowledge base results filtered by score threshold
*For any* knowledge base results, only results with relevance score >= 0.5 should be included in the response.
**Validates: Requirements 3.2**

### Property 10: Knowledge base responses include source attribution
*For any* knowledge base results included in a response, the response should contain source attribution with document names and URLs.
**Validates: Requirements 3.3**

### Property 11: Knowledge base search displays tool indicator
*For any* knowledge base search in progress, the UI should display a tool status indicator with "🔍 Searching knowledge base" message.
**Validates: Requirements 3.4**

### Property 12: Session IDs are unique
*For any* two chat sessions, the generated session IDs should be different (unique).
**Validates: Requirements 4.1**

### Property 13: User messages stored in Memory
*For any* user message sent, the message should be stored in Bedrock Memory with the correct actor_id (sanitized phone) and session_id.
**Validates: Requirements 4.2**

### Property 14: AI responses stored in Memory
*For any* AI response generated, the response should be stored in Bedrock Memory with the correct actor_id and session_id.
**Validates: Requirements 4.3**

### Property 15: Agent retrieves last 5 conversation turns
*For any* new message processed by the agent, the system should retrieve exactly the last 5 conversation turns from Bedrock Memory (or fewer if less than 5 exist).
**Validates: Requirements 4.4**

### Property 16: Phone number sanitization removes special characters
*For any* phone number stored as actor_id, the phone number should have "+", "-", and " " characters removed.
**Validates: Requirements 4.5**

### Property 17: Timing preference triggers handoff workflow
*For any* student timing preference provided after consent, the system should execute the advisor handoff workflow.
**Validates: Requirements 5.3**

### Property 18: Handoff execution displays tool indicator
*For any* advisor handoff workflow execution, the UI should display a tool status indicator with "🤝 Processing handoff" message.
**Validates: Requirements 5.4**

### Property 19: Declining advisor connection continues conversation
*For any* student declining advisor connection, the conversation should continue without executing the handoff workflow.
**Validates: Requirements 5.5**

### Property 20: Handoff workflow searches Salesforce by phone
*For any* advisor handoff execution, the system should search Salesforce for a Lead matching the student's phone number.
**Validates: Requirements 6.1**

### Property 21: Found Lead status updated to Working
*For any* Lead found in Salesforce during handoff, the Lead Status should be updated from "New" to "Working".
**Validates: Requirements 6.2**

### Property 22: Status update creates linked Task
*For any* Lead status update during handoff, a Task record should be created with WhoId set to the Lead ID.
**Validates: Requirements 6.3**

### Property 23: Task Subject includes student name
*For any* Task created during handoff, the Subject should be formatted as "Chat Conversation - [Student FirstName LastName]".
**Validates: Requirements 6.4**

### Property 24: Task Description includes all required sections
*For any* Task created during handoff, the Description should include conversation summary, programs discussed, student concerns, and full chat transcript.
**Validates: Requirements 6.5**

### Property 25: Task fields set to default values
*For any* Task created during handoff, Status should be "Not Started", Priority should be "Normal", and ActivityDate should be today's date.
**Validates: Requirements 6.6**

### Property 26: Handoff workflow queues WhatsApp message
*For any* advisor handoff execution, a WhatsApp message should be queued to the SQS queue.
**Validates: Requirements 7.1**

### Property 27: Queued message includes required fields
*For any* message queued to SQS, the message should include phone number, personalized message text, and timing preference.
**Validates: Requirements 7.2**

### Property 28: WhatsApp Lambda sends via Twilio
*For any* SQS message processed by the WhatsApp Lambda, the message should be sent via the Twilio WhatsApp API.
**Validates: Requirements 7.3**

### Property 29: Sent messages logged to tracking table
*For any* WhatsApp message sent, the message ID and delivery status should be logged to the WhatsAppMessageTracking DynamoDB table.
**Validates: Requirements 7.4**

### Property 30: New session checks for existing record
*For any* new chat session started, the system should check the WhatsappSessions DynamoDB table for an existing record by phone number.
**Validates: Requirements 8.1**

### Property 31: Existing user session array updated
*For any* existing session record found, the new session_id should be appended to the sessions array and latest_session_id should be updated.
**Validates: Requirements 8.2**

### Property 32: New user record created with correct structure
*For any* new user (no existing session record), a record should be created with phone_number as partition key, sessions array containing the session_id, and latest_session_id set to the session_id.
**Validates: Requirements 8.3**

### Property 33: Session updates set timestamp fields
*For any* session record update, web_app_last_connect_date should be set to the current date and web_app_last_connect_time should be set to the current time.
**Validates: Requirements 8.4**

### Property 34: Agent requests retrieve session record
*For any* agent request processed, the system should retrieve the session record from DynamoDB.
**Validates: Requirements 8.5**

### Property 35: Message send establishes SSE connection
*For any* message sent from the frontend to the agent, an SSE connection should be established to the agent proxy Lambda.
**Validates: Requirements 9.1**

### Property 36: Chunks forwarded as SSE events
*For any* chunk received by the agent proxy Lambda from AgentCore, the chunk should be forwarded as an SSE event with "data:" prefix.
**Validates: Requirements 9.2**

### Property 37: SSE events normalized to standard type
*For any* SSE event received by the frontend, the event should be parsed and normalized to a standard AgentStreamEvent type.
**Validates: Requirements 9.3**

### Property 38: Response events append to streaming message
*For any* "response" event received, the content should be appended to the current streaming message.
**Validates: Requirements 9.4**

### Property 39: Final events complete message and clear state
*For any* "final" event received, the complete message should be added to the messages array and the streaming state should be cleared.
**Validates: Requirements 9.5**

### Property 40: Tool status events display indicator
*For any* "tool_status" event received, the tool indicator should be displayed with the specified icon and message.
**Validates: Requirements 9.6**

### Property 41: Error events hide technical details
*For any* "error" event received, the displayed error message should be user-friendly and should not expose technical details.
**Validates: Requirements 9.7**

### Property 42: Knowledge base indicators use university short name
*For any* knowledge base search indicator displayed, the message should include the UNIVERSITY_SHORT_NAME.
**Validates: Requirements 11.2**

### Property 43: Lambda errors logged to CloudWatch
*For any* error encountered in a Lambda function, the error details should be logged to CloudWatch with appropriate log level.
**Validates: Requirements 12.1**

### Property 44: Proxy errors send error events
*For any* error encountered in the agent proxy Lambda, an error event should be sent to the frontend with a user-friendly message.
**Validates: Requirements 12.5**

## Error Handling

### Error Categories

**1. External Service Failures**
- **Salesforce Connection Errors**: When Salesforce API is unavailable or credentials are invalid
  - Strategy: Return user-friendly message to frontend, log technical details to CloudWatch
  - Fallback: Allow user to continue chatting, retry Lead creation on next handoff attempt
  
- **Twilio API Errors**: When WhatsApp message sending fails
  - Strategy: Log error to CloudWatch, rely on SQS retry policy (3 retries with exponential backoff)
  - Fallback: Message moves to dead-letter queue after max retries, alert administrators
  
- **Knowledge Base Unavailability**: When Bedrock Knowledge Base is down or returns errors
  - Strategy: Agent provides graceful fallback response without exposing error
  - Fallback: Agent continues conversation using general knowledge, logs error to CloudWatch

**2. Data Validation Errors**
- **Invalid Form Data**: Empty required fields, invalid email/phone format
  - Strategy: Client-side validation prevents submission, display field-specific error messages
  - Fallback: Server-side validation as backup, return 400 Bad Request with error details
  
- **Invalid Phone Number Format**: Phone number doesn't match E.164 format
  - Strategy: Sanitize phone number before storage, log warning if format is unusual
  - Fallback: Use sanitized version for actor_id, original version for display

**3. Infrastructure Errors**
- **Lambda Timeout**: Function exceeds execution time limit
  - Strategy: Set appropriate timeout values (30s for agent proxy, 15s for others)
  - Fallback: Return timeout error to client, log to CloudWatch for investigation
  
- **DynamoDB Throttling**: Read/write capacity exceeded
  - Strategy: Use on-demand billing mode to auto-scale
  - Fallback: Implement exponential backoff retry logic in code
  
- **SQS Queue Full**: Queue reaches message limit
  - Strategy: Set appropriate queue limits and retention period
  - Fallback: Alert administrators, scale up processing Lambda concurrency

**4. Agent Errors**
- **AgentCore Invocation Failure**: Agent runtime is unavailable
  - Strategy: Catch exception in agent proxy, return error event to frontend
  - Fallback: Display "Agent temporarily unavailable" message, suggest trying again
  
- **Tool Execution Failure**: Knowledge base or handoff tool fails
  - Strategy: Agent catches tool errors, provides graceful response to user
  - Fallback: Agent continues conversation without tool result, logs error
  
- **Memory Storage Failure**: Bedrock Memory API returns error
  - Strategy: Log error but continue processing (conversation history is nice-to-have)
  - Fallback: Agent operates without history context for that turn

**5. Frontend Errors**
- **SSE Connection Failure**: Network interruption during streaming
  - Strategy: Display connection error message, provide retry button
  - Fallback: User can send message again to re-establish connection
  
- **Event Parsing Error**: Malformed SSE event received
  - Strategy: Log error to console, skip malformed event, continue processing
  - Fallback: Display partial response if available, allow user to regenerate

### Error Logging Strategy

All errors should be logged to CloudWatch with structured format:
```json
{
  "timestamp": "ISO-8601",
  "level": "ERROR",
  "component": "form_submission_lambda | agent_proxy | whatsapp_sender | agent",
  "error_type": "SalesforceConnectionError | TwilioAPIError | ...",
  "error_message": "Human-readable description",
  "error_details": {
    "stack_trace": "...",
    "request_id": "...",
    "user_context": {
      "phone_number": "...",
      "session_id": "..."
    }
  }
}
```

### User-Facing Error Messages

Never expose technical details to users. Use friendly, actionable messages:
- ❌ "Salesforce API returned 401 Unauthorized"
- ✅ "We're having trouble saving your information. Please try again in a moment."

- ❌ "Knowledge Base vector search timeout after 30s"
- ✅ "I'm having trouble finding that information right now. Let me help you in another way."

- ❌ "Lambda function exceeded memory limit"
- ✅ "Something went wrong. Please refresh the page and try again."

## Testing Strategy

### Unit Testing

**Frontend Unit Tests** (Jest + React Testing Library):
- Form validation logic (empty fields, email format, phone format)
- Event normalization functions (SSE event parsing)
- Phone number sanitization utility
- Message state management
- Scroll behavior hooks

**Backend Unit Tests** (pytest):
- Salesforce connection and Lead creation
- Twilio message formatting
- DynamoDB session tracking logic
- Phone number sanitization
- Event formatting for SSE

**Agent Unit Tests** (pytest):
- Tool input/output validation
- Conversation history formatting
- Session context management
- Error handling in tools

### Property-Based Testing

**Property Testing Framework**: 
- Frontend: fast-check (TypeScript)
- Backend/Agent: Hypothesis (Python)

**Configuration**: Each property-based test should run a minimum of 100 iterations.

**Test Tagging**: Each property-based test must include a comment explicitly referencing the correctness property:
```python
# Feature: ai-admissions-agent, Property 1: Form validation rejects empty required fields
@given(form_data_with_empty_fields())
def test_form_validation_rejects_empty_fields(form_data):
    ...
```

**Key Property Tests**:

1. **Form Validation Properties**:
   - Generate random form data with various combinations of empty/filled fields
   - Verify validation correctly identifies missing required fields
   - Verify valid data passes validation

2. **Phone Sanitization Properties**:
   - Generate random phone numbers with various formats (+1-555-123-4567, +15551234567, etc.)
   - Verify sanitization removes all "+", "-", and " " characters
   - Verify sanitized result contains only digits

3. **Knowledge Base Filtering Properties**:
   - Generate random knowledge base results with scores from 0.0 to 1.0
   - Verify only results with score >= 0.5 are included
   - Verify results are sorted by score descending

4. **Session Tracking Properties**:
   - Generate random session IDs and phone numbers
   - Verify session records are created/updated correctly
   - Verify session arrays maintain uniqueness

5. **Event Normalization Properties**:
   - Generate random SSE event formats (various JSON structures)
   - Verify all formats are normalized to standard AgentStreamEvent types
   - Verify no data loss during normalization

6. **Memory Storage Properties**:
   - Generate random messages and conversation histories
   - Verify messages are stored with correct actor_id and session_id
   - Verify retrieval returns exactly last N turns

7. **Task Creation Properties**:
   - Generate random conversation data (summaries, programs, concerns, transcripts)
   - Verify Task Description includes all required sections
   - Verify Task fields are set to correct default values

8. **Error Message Properties**:
   - Generate random error objects with technical details
   - Verify user-facing messages don't contain stack traces, API keys, or internal paths
   - Verify all errors are logged to CloudWatch

### Integration Testing

**API Integration Tests**:
- Form submission → Salesforce Lead creation (end-to-end)
- Agent message → Knowledge Base retrieval → Response (end-to-end)
- Advisor handoff → Salesforce update → Task creation → WhatsApp queue (end-to-end)
- SQS message → WhatsApp Lambda → Twilio API → Tracking table (end-to-end)

**Frontend Integration Tests** (Playwright):
- User fills form → submits → chat opens with greeting
- User sends message → receives streaming response
- User clicks regenerate → receives new response
- Tool indicators appear during knowledge base search and handoff

**Infrastructure Integration Tests**:
- CDK deployment creates all resources
- Lambda functions can access DynamoDB tables
- Lambda functions can invoke AgentCore
- API Gateway CORS configuration allows frontend requests

### End-to-End Testing

**Complete User Journey**:
1. Visit landing page
2. Fill and submit inquiry form
3. Verify Salesforce Lead created
4. Chat opens with personalized greeting
5. Ask factual question
6. Verify knowledge base search indicator appears
7. Receive response with source attribution
8. Continue conversation (4-6 exchanges)
9. Agent offers advisor connection
10. Consent and provide timing preference
11. Verify handoff indicator appears
12. Verify Salesforce Lead status updated to "Working"
13. Verify Task created with conversation summary
14. Verify WhatsApp message received

**Error Scenario Testing**:
- Salesforce unavailable during form submission
- Knowledge Base unavailable during question
- Twilio unavailable during WhatsApp send
- Network interruption during streaming
- Invalid form data submission

### Performance Testing

**Load Testing**:
- Concurrent form submissions (target: 100 req/s)
- Concurrent chat sessions (target: 50 concurrent users)
- Knowledge Base query latency (target: < 2s p95)
- Agent response time (target: < 5s for first token)

**Stress Testing**:
- Large conversation histories (50+ turns)
- Knowledge Base with 1000+ documents
- SQS queue with 10,000+ messages
- DynamoDB with 100,000+ session records

### Monitoring and Observability

**CloudWatch Metrics**:
- Lambda invocation count, duration, errors
- API Gateway request count, latency, 4xx/5xx errors
- DynamoDB read/write capacity, throttles
- SQS queue depth, message age
- Bedrock AgentCore invocations, latency

**CloudWatch Alarms**:
- Lambda error rate > 5%
- API Gateway 5xx error rate > 1%
- SQS queue depth > 1000 messages
- DynamoDB throttling events
- Agent response time > 10s

**CloudWatch Dashboards**:
- Real-time system health overview
- User engagement metrics (sessions, messages, handoffs)
- Error rates by component
- Latency percentiles (p50, p95, p99)

**Distributed Tracing** (AWS X-Ray):
- Trace requests from frontend through all backend components
- Identify bottlenecks and slow operations
- Visualize service dependencies
