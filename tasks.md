# Implementation Plan

- [x] 1. Set up AWS CDK infrastructure project
  - Initialize CDK project with TypeScript
  - Create directory structure for Lambda functions and layers
  - Set up tsconfig.json and cdk.json configuration files
  - _Requirements: 10.1-10.9_

- [x] 2. Implement core AWS infrastructure with CDK
  - [x] 2.1 Create S3 bucket for knowledge base documents with versioning
    - Define S3 bucket construct with versioning enabled
    - Configure bucket policies for Bedrock access
    - _Requirements: 10.1_

  - [x] 2.2 Create DynamoDB tables for session and message tracking
    - Define WhatsappSessions table with phone_number as partition key
    - Define WhatsAppMessageTracking table with eum_msg_id as partition key
    - Configure on-demand billing mode
    - _Requirements: 10.2, 8.1-8.4_

  - [x] 2.3 Create SQS queue for WhatsApp messages with dead-letter queue
    - Define SQS queue construct with visibility timeout
    - Configure dead-letter queue for failed messages
    - Set up retry policy (3 retries with exponential backoff)
    - _Requirements: 10.3, 7.1_

  - [x] 2.4 Create IAM role for AgentCore with required permissions
    - Define IAM role with trust policy for Bedrock AgentCore
    - Attach policies for Bedrock, S3, DynamoDB, SQS access
    - _Requirements: 10.8_

  - [x] 2.5 Create ECR repository for AgentCore container images
    - Define ECR repository construct
    - Configure lifecycle policies for image retention
    - _Requirements: 10.7_

- [x] 3. Create Lambda layers for external dependencies
  - [x] 3.1 Build Salesforce Lambda layer
    - Create layer directory structure
    - Install simple-salesforce and requests packages
    - Package layer as zip file
    - _Requirements: 10.6_

  - [x] 3.2 Build Twilio Lambda layer
    - Create layer directory structure
    - Install twilio and aiohttp packages
    - Package layer as zip file
    - _Requirements: 10.6_

- [x] 4. Implement Form Submission Lambda function
  - [x] 4.1 Create form submission Lambda handler
    - Parse API Gateway event to extract form data
    - Validate required fields are present
    - Connect to Salesforce using credentials from environment
    - Create Lead record with mapped fields
    - Return success/error response
    - _Requirements: 1.4_

  - [x] 4.2 Write property test for form validation
    - **Property 1: Form validation rejects empty required fields**
    - **Validates: Requirements 1.3**

  - [x] 4.3 Write property test for Lead creation
    - **Property 2: Valid form submission creates Salesforce Lead**
    - **Validates: Requirements 1.4**

  - [x] 4.4 Write unit tests for error handling
    - Test Salesforce connection failure scenarios
    - Test invalid form data handling
    - Verify CloudWatch logging
    - _Requirements: 12.1, 12.2_

- [x] 5. Implement WhatsApp Sender Lambda function
  - [x] 5.1 Create WhatsApp sender Lambda handler
    - Parse SQS event to extract message data
    - Connect to Twilio API using credentials
    - Send WhatsApp message via Twilio
    - Log message ID and status to DynamoDB tracking table
    - Handle errors and log to CloudWatch
    - _Requirements: 7.3, 7.4_

  - [x] 5.2 Write property test for message sending
    - **Property 28: WhatsApp Lambda sends via Twilio**
    - **Validates: Requirements 7.3**

  - [x] 5.3 Write property test for message tracking
    - **Property 29: Sent messages logged to tracking table**
    - **Validates: Requirements 7.4**

  - [x] 5.4 Write unit tests for error handling
    - Test Twilio API failure scenarios
    - Verify error logging to CloudWatch
    - Test SQS retry behavior
    - _Requirements: 12.4_

- [x] 6. Implement Agent Proxy Lambda function
  - [x] 6.1 Create agent proxy Lambda handler with streaming
    - Use awslambda.streamifyResponse for SSE streaming
    - Parse request body to extract prompt, session_id, phone_number
    - Invoke Bedrock AgentCore with streaming enabled
    - Forward chunks as SSE events with "data:" prefix
    - Handle errors and send error events
    - _Requirements: 9.1, 9.2_

  - [x] 6.2 Write property test for SSE event forwarding
    - **Property 36: Chunks forwarded as SSE events**
    - **Validates: Requirements 9.2**

  - [x] 6.3 Write property test for error handling
    - **Property 44: Proxy errors send error events**
    - **Validates: Requirements 12.5**

  - [x] 6.4 Write unit tests for streaming behavior
    - Test SSE connection establishment
    - Test chunk forwarding
    - Test error scenarios
    - _Requirements: 9.1, 9.2_

- [x] 7. Create API Gateway for form submission
  - [x] 7.1 Define API Gateway REST API with CDK
    - Create REST API construct
    - Define POST endpoint for form submission
    - Integrate with Form Submission Lambda
    - Configure CORS for frontend domain
    - _Requirements: 10.5_

  - [x] 7.2 Create Lambda function URL for agent proxy
    - Define function URL for agent proxy Lambda
    - Enable streaming response mode
    - Configure CORS headers
    - _Requirements: 10.9_

- [x] 8. Deploy CDK stack and capture outputs
  - Run cdk synth to validate stack
  - Run cdk deploy to create resources
  - Capture and save output values (API URLs, ARNs, table names)
  - _Requirements: 10.9_

- [x] 9. Set up Bedrock Knowledge Base
  - Create Bedrock Knowledge Base in AWS console
  - Configure S3 data source pointing to CDK-created bucket
  - Select Titan Embeddings G1 - Text model
  - Configure vector store settings
  - Save Knowledge Base ID
  - _Requirements: 3.1_

- [x] 10. Upload knowledge base documents
  - Prepare university documents (PDFs, DOCX, TXT)
  - Upload documents to S3 bucket
  - Sync Knowledge Base in Bedrock console
  - Verify documents are indexed
  - _Requirements: 3.1_

- [x] 11. Implement agent session utilities
  - [x] 11.1 Create phone number sanitization function
    - Implement sanitize_phone_for_actor_id function
    - Remove "+", "-", and " " characters
    - _Requirements: 4.5_

  - [x] 11.2 Write property test for phone sanitization
    - **Property 16: Phone number sanitization removes special characters**
    - **Validates: Requirements 4.5**

  - [x] 11.3 Create conversation history retrieval function
    - Implement fetch_conversation_history function
    - Use Bedrock Memory client to list events
    - Filter by actor_id and session_id
    - Retrieve last N turns (configurable via MAX_HISTORY_TURNS)
    - Format as "User: ...\nAssistant: ..." string
    - _Requirements: 4.4_

  - [x] 11.4 Write property test for history retrieval
    - **Property 15: Agent retrieves last 5 conversation turns**
    - **Validates: Requirements 4.4**

  - [x] 11.5 Create session tracking functions
    - Implement track_user_session function
    - Check DynamoDB for existing session record
    - Create new record or update existing with session_id
    - Set timestamp fields
    - _Requirements: 8.1-8.4_

  - [x] 11.6 Write property test for session tracking
    - **Property 30: New session checks for existing record**
    - **Property 31: Existing user session array updated**
    - **Property 32: New user record created with correct structure**
    - **Property 33: Session updates set timestamp fields**
    - **Validates: Requirements 8.1-8.4**

- [x] 12. Implement Salesforce integration tools
  - [x] 12.1 Create Salesforce connection helper
    - Implement get_salesforce_connection function
    - Use simple-salesforce library with credentials from environment
    - Handle connection errors gracefully
    - _Requirements: 6.1_

  - [x] 12.2 Create Lead search function
    - Implement search_lead_by_phone function
    - Query Salesforce for Lead by Phone field
    - Return Lead ID if found
    - _Requirements: 6.1_

  - [x] 12.3 Create Lead update function
    - Implement update_lead_status function
    - Update Lead Status field to "Working"
    - Handle errors and log to CloudWatch
    - _Requirements: 6.2_

  - [x] 12.4 Create Task creation function
    - Implement create_task_with_full_history function
    - Format Task Subject with student name
    - Format Task Description with summary, programs, concerns, transcript
    - Set Task fields (Status, Priority, ActivityDate, WhoId)
    - Create Task in Salesforce
    - _Requirements: 6.3-6.6_

  - [x] 12.5 Write property test for Task creation
    - **Property 23: Task Subject includes student name**
    - **Property 24: Task Description includes all required sections**
    - **Property 25: Task fields set to default values**
    - **Validates: Requirements 6.4-6.6**

- [x] 13. Implement WhatsApp messaging tool
  - [x] 13.1 Create SQS message queueing function
    - Implement queue_whatsapp_message function
    - Format message payload with phone, text, timing preference
    - Send message to SQS queue
    - _Requirements: 7.1, 7.2_

  - [x] 13.2 Write property test for message queueing
    - **Property 26: Handoff workflow queues WhatsApp message**
    - **Property 27: Queued message includes required fields**
    - **Validates: Requirements 7.1, 7.2**

- [x] 14. Implement Knowledge Base retrieval tool
  - [x] 14.1 Create knowledge base search function
    - Implement retrieve_university_info tool function
    - Use boto3 bedrock-agent-runtime client
    - Call retrieve API with query text
    - Filter results by score threshold (0.5)
    - Extract source attribution (document name, URL)
    - Format results as string
    - _Requirements: 3.1-3.3_

  - [x] 14.2 Write property test for score filtering
    - **Property 9: Knowledge base results filtered by score threshold**
    - **Validates: Requirements 3.2**

  - [x] 14.3 Write property test for source attribution
    - **Property 10: Knowledge base responses include source attribution**
    - **Validates: Requirements 3.3**

  - [x] 14.4 Write unit tests for error handling
    - Test Knowledge Base unavailability
    - Verify graceful fallback
    - Verify error logging
    - _Requirements: 12.3_

- [x] 15. Implement advisor handoff orchestration tool
  - [x] 15.1 Create context management functions
    - Implement set_context function for module-level storage
    - Store phone_number and session_id for tool access
    - _Requirements: 6.1_

  - [x] 15.2 Create advisor handoff tool function
    - Implement complete_advisor_handoff tool function
    - Retrieve full conversation history from Bedrock Memory
    - Search Salesforce for Lead by phone number
    - Update Lead status to "Working"
    - Create Task with summary and transcript
    - Queue WhatsApp message to SQS
    - Return success message
    - _Requirements: 5.3, 6.1-6.6, 7.1_

  - [x] 15.3 Write property test for handoff workflow
    - **Property 17: Timing preference triggers handoff workflow**
    - **Property 20: Handoff workflow searches Salesforce by phone**
    - **Property 21: Found Lead status updated to Working**
    - **Property 22: Status update creates linked Task**
    - **Validates: Requirements 5.3, 6.1-6.3**

- [x] 16. Implement main agent with Strands framework
  - [x] 16.1 Create agent system prompt
    - Write conversational system prompt for Nemo
    - Define personality (friendly, consultative, not robotic)
    - Specify conversation phases (rapport, exploration, knowledge sharing, advisor transition)
    - Include guidelines for advisor handoff timing
    - Reference UNIVERSITY_NAME in context
    - _Requirements: 2.1, 11.5_

  - [x] 16.2 Create agent instance with tools
    - Import Strands Agent and BedrockModel
    - Configure Claude Sonnet 4.5 model
    - Register retrieve_university_info tool
    - Register complete_advisor_handoff tool
    - _Requirements: 3.1, 5.3_

  - [x] 16.3 Implement agent entrypoint function
    - Create @app.entrypoint async function
    - Parse payload (prompt, session_id, phone_number, system_message)
    - Track session in DynamoDB
    - Retrieve conversation history from Memory
    - Store user message in Memory
    - Set context for tools (phone_number, session_id)
    - Enhance prompt with history and system message
    - Stream agent response with event handling
    - Store assistant response in Memory
    - Yield events: {response}, {thinking}, {tool_result}, {final_result}, {error}
    - _Requirements: 2.3, 4.2-4.4, 8.5_

  - [x] 16.4 Write property test for Memory storage
    - **Property 13: User messages stored in Memory**
    - **Property 14: AI responses stored in Memory**
    - **Validates: Requirements 4.2, 4.3**

  - [x] 16.5 Write property test for session ID uniqueness
    - **Property 12: Session IDs are unique**
    - **Validates: Requirements 4.1**

- [x] 17. Configure and deploy AgentCore
  - [x] 17.1 Create agent requirements.txt
    - List bedrock-agentcore, strands-agents, boto3, python-dotenv
    - List simple-salesforce, twilio
    - _Requirements: 6.1, 7.3_

  - [x] 17.2 Create agent environment file template
    - Define all required environment variables
    - Include AWS_REGION, AGENTCORE_MEMORY_ID, SESSIONS_TABLE_NAME
    - Include ENGLISH_KNOWLEDGE_BASE_ID, TWILIO_WHATSAPP_QUEUE_URL
    - Include Salesforce and Twilio credentials
    - Include university branding variables
    - _Requirements: 11.1_

  - [x] 17.3 Run agentcore configure
    - Execute agentcore configure command
    - Provide execution role ARN from CDK output
    - Provide ECR repository URI from CDK output
    - Enable short-term memory
    - Generate .bedrock_agentcore.yaml, Dockerfile, .dockerignore
    - _Requirements: 10.8_

  - [x] 17.4 Create agent launch script
    - Write bash script to load environment variables
    - Execute agentcore launch with all environment variables
    - _Requirements: 11.1_

  - [x] 17.5 Deploy agent to AgentCore
    - Run launch script to build and push Docker image
    - Deploy to Bedrock AgentCore
    - Capture Agent Runtime ARN
    - _Requirements: 10.9_

- [x] 18. Update CDK stack with Agent Runtime ARN
  - Update environment variables with Agent Runtime ARN
  - Update environment variables with Knowledge Base ID
  - Redeploy CDK stack
  - Capture updated outputs (Agent Proxy Function URL)
  - _Requirements: 10.9_

- [x] 19. Initialize Next.js frontend project
  - Create Next.js 15 project with TypeScript and Tailwind CSS
  - Install dependencies (Radix UI, react-markdown, react-hook-form, zod)
  - Set up project structure (app, components, lib directories)
  - _Requirements: 1.1_

- [x] 20. Create frontend configuration and utilities
  - [x] 20.1 Create configuration file
    - Define config object with agentProxyUrl and formSubmissionApi
    - Read from environment variables
    - _Requirements: 1.4, 9.1_

  - [x] 20.2 Create utility functions
    - Implement cn utility for className merging
    - Create date formatting utilities
    - _Requirements: 2.2_

  - [x] 20.3 Create scroll management hook
    - Implement use-stick-to-bottom hook
    - Track if user is at bottom of scroll container
    - Provide scrollToBottom function
    - _Requirements: 2.2_

- [x] 21. Implement SSE streaming client
  - [x] 21.1 Create agent event types
    - Define AgentStreamEvent type union
    - Define event types: response, tool_status, tool_result, final, error
    - _Requirements: 9.3_

  - [x] 21.2 Create event normalization function
    - Implement normalizeRawEvent function
    - Handle various backend event formats
    - Map to standard AgentStreamEvent types
    - _Requirements: 9.3_

  - [x] 21.3 Write property test for event normalization
    - **Property 37: SSE events normalized to standard type**
    - **Validates: Requirements 9.3**

  - [x] 21.4 Create streaming client function
    - Implement streamChatResponse async generator
    - Establish SSE connection to agent proxy
    - Parse SSE stream (data: lines)
    - Yield normalized events
    - Handle connection errors
    - _Requirements: 9.1, 9.2_

  - [x] 21.5 Write property test for SSE connection
    - **Property 35: Message send establishes SSE connection**
    - **Validates: Requirements 9.1**

- [x] 22. Create form submission API client
  - [x] 22.1 Implement form submission function
    - Create submitInquiryForm function
    - POST to form submission API with form data
    - Handle success and error responses
    - _Requirements: 1.4_

  - [x] 22.2 Write unit tests for API client
    - Test successful submission
    - Test error handling
    - Test network failures
    - _Requirements: 1.4_

- [x] 23. Implement base UI components
  - [x] 23.1 Create Button component
    - Implement Radix-based button with variants
    - Support primary, secondary, ghost variants
    - Support different sizes
    - _Requirements: 1.1_

  - [x] 23.2 Create Input component
    - Implement form input field with label
    - Support validation states
    - _Requirements: 1.2_

  - [x] 23.3 Create Card component
    - Implement card container with variants
    - Support glass-morphism styling
    - _Requirements: 1.1_

- [-] 24. Implement chat UI components
  - [x] 24.1 Create Message types
    - Define Message interface (id, type, content, timestamp, toolStatus)
    - Define ToolStatus interface (icon, message, state)
    - _Requirements: 2.2, 3.4_

  - [x] 24.2 Create ChatHeader component
    - Display "Nemo" title with university branding
    - Include close button
    - _Requirements: 2.1_

  - [ ] 24.3 Create ChatInput component
    - Text input with send button
    - Handle Enter key for submission
    - Disable during streaming
    - _Requirements: 2.2_

  - [ ] 24.4 Create Markdown renderer component
    - Use react-markdown with remark-gfm
    - Add syntax highlighting with rehype-highlight
    - Style code blocks and lists
    - _Requirements: 2.4_

  - [ ] 24.5 Create ChatMessage component
    - Display message bubble with user/AI styling
    - Show timestamp
    - Render markdown for AI messages
    - Include regenerate button for AI messages
    - Display tool status indicator if present
    - _Requirements: 2.2, 2.4, 2.5, 3.4_

  - [ ] 24.6 Write property test for message display
    - **Property 4: User messages display with correct styling**
    - **Property 6: Completed AI messages include regenerate button**
    - **Validates: Requirements 2.2, 2.4**

  - [ ] 24.7 Create EmptyState component
    - Display welcome message
    - Show suggested questions
    - _Requirements: 2.6_

  - [ ] 24.8 Create Loader component
    - Animated loading dots
    - _Requirements: 2.3_

  - [ ] 24.9 Create ScrollButton component
    - Floating button to scroll to bottom
    - Only visible when not at bottom
    - _Requirements: 2.2_

  - [ ] 24.10 Create ToolCard component
    - Display tool usage indicator with icon and message
    - Support running and completed states
    - _Requirements: 3.4, 5.4_

  - [ ] 24.11 Write property test for tool indicators
    - **Property 11: Knowledge base search displays tool indicator**
    - **Property 18: Handoff execution displays tool indicator**
    - **Property 40: Tool status events display indicator**
    - **Validates: Requirements 3.4, 5.4, 9.6**

- [ ] 25. Implement main chat interface component
  - [ ] 25.1 Create NemoChatInterface component
    - Set up state management (messages, streaming, tool status, sessionId)
    - Initialize sessionId on mount
    - Implement handleSendMessage function
    - Implement handleRegenerate function
    - Implement auto-scroll logic
    - Render chat header, message list, chat input
    - Render empty state when no messages
    - _Requirements: 2.1-2.6, 4.1_

  - [ ] 25.2 Write property test for streaming behavior
    - **Property 5: AI responses stream incrementally**
    - **Property 38: Response events append to streaming message**
    - **Property 39: Final events complete message and clear state**
    - **Validates: Requirements 2.3, 9.4, 9.5**

  - [ ] 25.3 Write property test for regeneration
    - **Property 7: Regenerate button triggers new response**
    - **Validates: Requirements 2.5**

  - [ ] 25.4 Write property test for error handling
    - **Property 41: Error events hide technical details**
    - **Validates: Requirements 9.7**

- [ ] 26. Implement inquiry form component
  - [ ] 26.1 Create InquiryForm component
    - Define form fields (firstName, lastName, email, cellPhone, homePhone, headquarters, programType)
    - Implement form validation with react-hook-form and zod
    - Handle form submission
    - Display validation errors
    - Show loading state during submission
    - _Requirements: 1.2, 1.3_

  - [ ] 26.2 Write property test for form validation
    - **Property 1: Form validation rejects empty required fields**
    - **Validates: Requirements 1.3**

  - [ ] 26.3 Write unit tests for form submission
    - Test successful submission opens chat
    - Test error handling
    - _Requirements: 1.4, 1.5_

- [ ] 27. Implement landing page component
  - [ ] 27.1 Create MapuaLandingPage component
    - Create hero section with university image and tagline
    - Create program highlights section
    - Integrate inquiry form
    - Create footer with links
    - _Requirements: 1.1_

  - [ ] 27.2 Write property test for chat opening
    - **Property 3: Successful Lead creation opens chat with context**
    - **Validates: Requirements 1.5**

- [ ] 28. Create main page and layout
  - [ ] 28.1 Create app/page.tsx
    - Import and render landing page component
    - Handle form submission to open chat
    - Pass form context to chat interface
    - _Requirements: 1.1, 1.5_

  - [ ] 28.2 Create app/layout.tsx
    - Set up root layout with metadata
    - Configure theme provider
    - Import global styles
    - _Requirements: 1.1_

  - [ ] 28.3 Create app/globals.css
    - Add Tailwind directives
    - Define CSS variables for university colors
    - Add glass-morphism effects
    - Add animation keyframes
    - _Requirements: 11.4_

- [ ] 29. Add static assets and branding
  - Add university logos to public directory
  - Add hero image to public directory
  - Add Nemo logo to public directory
  - _Requirements: 11.3_

- [ ] 30. Create environment configuration files
  - Create .env.local for frontend with API URLs
  - Create .env for backend CDK with credentials
  - Create .env for agent with all required variables
  - Create .env.example templates for all
  - _Requirements: 11.1_

- [ ] 31. Test complete user journey end-to-end
  - Visit landing page
  - Fill and submit inquiry form
  - Verify Salesforce Lead created
  - Verify chat opens with greeting
  - Send message and verify streaming response
  - Ask factual question and verify knowledge base search
  - Verify source attribution in response
  - Request advisor connection
  - Verify handoff workflow executes
  - Verify Salesforce Lead updated and Task created
  - Verify WhatsApp message sent
  - _Requirements: 1.1-1.5, 2.1-2.6, 3.1-3.4, 5.1-5.5, 6.1-6.6, 7.1-7.4_

- [ ] 32. Set up monitoring and logging
  - Create CloudWatch dashboard for system metrics
  - Set up CloudWatch alarms for error rates
  - Configure X-Ray tracing for distributed tracing
  - Verify all Lambda functions log to CloudWatch
  - _Requirements: 12.1_

- [ ] 33. Create deployment documentation
  - Document CDK deployment steps
  - Document AgentCore deployment steps
  - Document frontend deployment steps
  - Document environment variable configuration
  - Document customization for different universities
  - _Requirements: 10.1-10.9, 11.1-11.5_
