# Requirements Document

## Introduction

The AI-Powered University Admissions Agent is a conversational AI platform that helps prospective university students explore programs, admissions requirements, and campus life through natural dialogue. The system combines AWS Bedrock AgentCore with a Next.js frontend to provide an intelligent chatbot experience that captures leads in Salesforce CRM and facilitates connections with enrollment advisors through automated WhatsApp follow-ups.

## Glossary

- **Nemo**: The conversational AI agent that interacts with prospective students
- **AgentCore**: AWS Bedrock service that hosts and runs the AI agent
- **Knowledge Base**: AWS Bedrock vector database containing university information documents
- **Lead**: A Salesforce CRM record representing a prospective student
- **Task**: A Salesforce CRM record representing a follow-up activity assigned to an enrollment advisor
- **Session**: A conversation instance tracked by session ID and phone number
- **Advisor Handoff**: The process of transitioning a student from chatbot to human enrollment advisor
- **System Message**: A message containing form context passed to the agent at conversation start
- **Streaming Response**: Real-time delivery of AI responses as they are generated
- **Tool**: A function the AI agent can call to perform actions (search knowledge base, update CRM, send messages)
- **Actor ID**: A sanitized phone number used to identify users in Bedrock Memory
- **Memory**: Bedrock AgentCore service that stores conversation history

## Requirements

### Requirement 1

**User Story:** As a prospective student, I want to fill out an inquiry form with my contact information and interests, so that the university can capture my information and start a conversation with me.

#### Acceptance Criteria

1. WHEN a user visits the landing page THEN the system SHALL display a modern university landing page with hero section, program highlights, and inquiry form
2. WHEN a user fills out the inquiry form THEN the system SHALL collect firstName, lastName, email, cellPhone, homePhone (optional), headquarters (campus), and programType
3. WHEN a user submits the inquiry form THEN the system SHALL validate all required fields are non-empty
4. WHEN the inquiry form is submitted with valid data THEN the system SHALL create a Lead record in Salesforce CRM with LeadSource set to "Web Form - Admissions" and Status set to "New"
5. WHEN the Salesforce Lead is created successfully THEN the system SHALL open the chat interface with a system message containing the form context

### Requirement 2

**User Story:** As a prospective student, I want to have natural conversations with an AI assistant about university programs, so that I can get my questions answered quickly without waiting for a human advisor.

#### Acceptance Criteria

1. WHEN the chat interface opens THEN the system SHALL greet the student by firstName and introduce itself as Nemo
2. WHEN a student sends a message THEN the system SHALL display the message in a user-styled bubble with timestamp
3. WHEN Nemo generates a response THEN the system SHALL stream the response with a typewriter effect
4. WHEN Nemo completes a response THEN the system SHALL display the message in an AI-styled bubble with a regenerate button
5. WHEN a student clicks the regenerate button THEN the system SHALL regenerate the last AI response
6. WHEN the chat has no messages THEN the system SHALL display an empty state with welcome message and suggested questions

### Requirement 3

**User Story:** As a prospective student, I want the AI assistant to answer factual questions about programs, admissions, and campus life, so that I can make informed decisions about my education.

#### Acceptance Criteria

1. WHEN a student asks a factual question about university information THEN the system SHALL search the Knowledge Base using vector similarity search
2. WHEN the Knowledge Base returns results THEN the system SHALL filter results with relevance score below 0.5 threshold
3. WHEN the Knowledge Base returns relevant results THEN the system SHALL include source attribution with document names and URLs in the response
4. WHEN the Knowledge Base search is in progress THEN the system SHALL display a tool status indicator with "🔍 Searching knowledge base" message
5. WHEN the Knowledge Base is unavailable THEN the system SHALL provide a graceful fallback response without exposing technical errors

### Requirement 4

**User Story:** As a prospective student, I want the AI assistant to remember our conversation context, so that I don't have to repeat information and the conversation feels natural.

#### Acceptance Criteria

1. WHEN a student starts a chat session THEN the system SHALL generate a unique session ID
2. WHEN a student sends a message THEN the system SHALL store the message in Bedrock Memory with actor_id (sanitized phone number) and session_id
3. WHEN Nemo generates a response THEN the system SHALL store the response in Bedrock Memory with actor_id and session_id
4. WHEN Nemo processes a new message THEN the system SHALL retrieve the last 5 conversation turns from Bedrock Memory
5. WHEN a student's phone number is stored as actor_id THEN the system SHALL sanitize the phone number by removing "+", "-", and " " characters

### Requirement 5

**User Story:** As a prospective student, I want to connect with a human enrollment advisor when I'm ready, so that I can get personalized guidance and move forward with my application.

#### Acceptance Criteria

1. WHEN a student has engaged in 4-6 meaningful message exchanges with Nemo THEN the system SHALL offer to connect the student with an enrollment advisor
2. WHEN a student consents to advisor connection THEN the system SHALL ask for timing preference (within 2 hours or during business hours)
3. WHEN a student provides timing preference THEN the system SHALL execute the advisor handoff workflow
4. WHEN the advisor handoff workflow executes THEN the system SHALL display a tool status indicator with "🤝 Processing handoff" message
5. WHEN a student declines advisor connection THEN the system SHALL respect the decision and continue the conversation

### Requirement 6

**User Story:** As an enrollment advisor, I want the system to automatically update lead records and create tasks with conversation summaries, so that I have complete context when I contact prospective students.

#### Acceptance Criteria

1. WHEN the advisor handoff workflow executes THEN the system SHALL search Salesforce for the Lead by phone number
2. WHEN the Lead is found in Salesforce THEN the system SHALL update the Lead Status from "New" to "Working"
3. WHEN the Lead Status is updated THEN the system SHALL create a Task record linked to the Lead with WhoId set to the Lead ID
4. WHEN the Task is created THEN the system SHALL set the Subject to "Chat Conversation - [Student FirstName LastName]"
5. WHEN the Task is created THEN the system SHALL set the Description to include conversation summary, programs discussed, student concerns, and full chat transcript
6. WHEN the Task is created THEN the system SHALL set Status to "Not Started", Priority to "Normal", and ActivityDate to today's date

### Requirement 7

**User Story:** As a prospective student, I want to receive a personalized WhatsApp message after requesting advisor contact, so that I have confirmation and know what to expect next.

#### Acceptance Criteria

1. WHEN the advisor handoff workflow executes THEN the system SHALL queue a WhatsApp message to the SQS queue
2. WHEN a message is queued to SQS THEN the system SHALL include the student's phone number, personalized message text, and timing preference
3. WHEN the WhatsApp Lambda processes a message from SQS THEN the system SHALL send the message via Twilio WhatsApp API
4. WHEN the WhatsApp message is sent THEN the system SHALL log the message ID and delivery status to the WhatsAppMessageTracking DynamoDB table
5. WHEN the Twilio API returns an error THEN the system SHALL log the error to CloudWatch and retry according to SQS retry policy

### Requirement 8

**User Story:** As a system administrator, I want the system to track user sessions across multiple interactions, so that we can analyze engagement patterns and maintain conversation continuity.

#### Acceptance Criteria

1. WHEN a student starts a chat session THEN the system SHALL check the WhatsappSessions DynamoDB table for an existing record by phone number
2. WHEN an existing session record is found THEN the system SHALL append the new session_id to the sessions array and update latest_session_id
3. WHEN no existing session record is found THEN the system SHALL create a new record with phone_number as partition key, sessions array containing the session_id, and latest_session_id set to the session_id
4. WHEN a session record is updated THEN the system SHALL set web_app_last_connect_date to the current date and web_app_last_connect_time to the current time
5. WHEN the agent processes a request THEN the system SHALL retrieve the session record to access conversation history

### Requirement 9

**User Story:** As a developer, I want the frontend to handle streaming responses gracefully, so that users experience smooth, real-time conversations without delays or errors.

#### Acceptance Criteria

1. WHEN the frontend sends a message to the agent THEN the system SHALL establish a Server-Sent Events (SSE) connection to the agent proxy Lambda
2. WHEN the agent proxy Lambda receives chunks from AgentCore THEN the system SHALL forward the chunks as SSE events with "data:" prefix
3. WHEN the frontend receives an SSE event THEN the system SHALL parse the event and normalize it to a standard AgentStreamEvent type
4. WHEN the frontend receives a "response" event THEN the system SHALL append the content to the current streaming message
5. WHEN the frontend receives a "final" event THEN the system SHALL add the complete message to the messages array and clear the streaming state
6. WHEN the frontend receives a "tool_status" event THEN the system SHALL display the tool indicator with the specified icon and message
7. WHEN the frontend receives an "error" event THEN the system SHALL display a user-friendly error message without exposing technical details

### Requirement 10

**User Story:** As a system administrator, I want the infrastructure to be deployed using Infrastructure as Code, so that the system is reproducible, maintainable, and follows AWS best practices.

#### Acceptance Criteria

1. WHEN the CDK stack is deployed THEN the system SHALL create an S3 bucket for knowledge base documents with versioning enabled
2. WHEN the CDK stack is deployed THEN the system SHALL create DynamoDB tables for WhatsappSessions and WhatsAppMessageTracking with on-demand billing
3. WHEN the CDK stack is deployed THEN the system SHALL create an SQS queue for WhatsApp messages with dead-letter queue configured
4. WHEN the CDK stack is deployed THEN the system SHALL create Lambda functions for form submission, WhatsApp sending, and agent proxy with appropriate IAM roles
5. WHEN the CDK stack is deployed THEN the system SHALL create an API Gateway REST API for form submission with CORS enabled for the frontend domain
6. WHEN the CDK stack is deployed THEN the system SHALL create Lambda layers for Salesforce and Twilio dependencies
7. WHEN the CDK stack is deployed THEN the system SHALL create an ECR repository for AgentCore container images
8. WHEN the CDK stack is deployed THEN the system SHALL create an IAM role for AgentCore with permissions for Bedrock, S3, DynamoDB, and SQS
9. WHEN the CDK stack is deployed THEN the system SHALL output the agent proxy function URL, form submission API URL, and other resource identifiers

### Requirement 11

**User Story:** As a university administrator, I want to customize the platform branding and content for my institution, so that the system reflects our unique identity and programs.

#### Acceptance Criteria

1. WHEN the system is configured THEN the system SHALL read UNIVERSITY_NAME and UNIVERSITY_SHORT_NAME from environment variables
2. WHEN Nemo generates responses THEN the system SHALL use the UNIVERSITY_SHORT_NAME in knowledge base search indicators
3. WHEN the landing page is rendered THEN the system SHALL display university-specific logos from the public assets directory
4. WHEN the landing page is rendered THEN the system SHALL apply university-specific colors from the global CSS variables
5. WHEN the agent system prompt is configured THEN the system SHALL reference the UNIVERSITY_NAME in the conversational context

### Requirement 12

**User Story:** As a system administrator, I want comprehensive error handling and logging, so that I can troubleshoot issues quickly and maintain system reliability.

#### Acceptance Criteria

1. WHEN any Lambda function encounters an error THEN the system SHALL log the error details to CloudWatch with appropriate log level
2. WHEN the Salesforce connection fails THEN the system SHALL return a user-friendly error message and log the technical details to CloudWatch
3. WHEN the Knowledge Base is unavailable THEN the system SHALL provide a fallback response and log the error to CloudWatch
4. WHEN the Twilio API fails THEN the system SHALL log the error to CloudWatch and allow SQS retry mechanism to handle retries
5. WHEN the agent proxy Lambda encounters an error THEN the system SHALL send an error event to the frontend with a user-friendly message
