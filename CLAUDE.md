# AI-Powered University Admissions Agent - Project Instructions

## Project Overview

This is an AI-powered conversational agent platform for university admissions built with AWS Bedrock AgentCore, Next.js 15, and integrated with Salesforce CRM and WhatsApp messaging.

**Agent Name:** Nemo
**Primary Model:** Claude Sonnet 4.5 (global.anthropic.claude-sonnet-4-5-20250929-v1:0)
**Framework:** AWS Bedrock AgentCore with Strands Agent SDK

## Use Context7 by Default

Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library ID and get library docs without me having to explicitly ask.

## Write local test suites

Write local unit test suites (using mock AWS data when necessary) in order to ensure that the logic of each section of the project is correct before moving on to deploying in AWS.

## Use Prompt Kit bulding blocks

Whenever possible, use Prompt Kit templates (https://www.prompt-kit.com/) when building frontend assets.

## Document as necessary

Make and edit relevant documentation (including CLAUDE.md files) as you go, to ensure that you can keep track of your work as you go.

## Architecture Overview

The system consists of three main layers:

### 1. Frontend Layer (Next.js 15)
- Modern landing page with inquiry form
- Real-time chat interface with Server-Sent Events (SSE) streaming
- React 19, TypeScript 5, Tailwind CSS 4
- Located in: `Frontend/admissions-chat/`

### 2. Backend Layer (AWS Infrastructure)
- AWS CDK for Infrastructure as Code
- Lambda Functions: Agent Proxy (Node.js 20), Form Submission (Python 3.12), WhatsApp Sender (Python 3.12)
- API Gateway for form submission endpoint
- DynamoDB tables: WhatsappSessions, WhatsAppMessageTracking
- SQS queue for WhatsApp message delivery
- S3 bucket for knowledge base documents
- Located in: `Backend/admissions-ai-agent/`

### 3. AI Agent Layer (Bedrock AgentCore)
- Strands-based conversational agent with streaming responses
- Bedrock Knowledge Base with vector search (Titan Embeddings)
- Bedrock Memory for conversation history (short-term, last 5 turns)
- Custom tools: Knowledge Base retrieval, Advisor handoff orchestration
- External integrations: Salesforce (simple-salesforce), Twilio WhatsApp API
- Located in: `Backend/admissions-ai-agent/AgentCore/`

## Key Technical Decisions

1. **Streaming Architecture**: Use SSE (Server-Sent Events) via Lambda Function URLs for real-time AI responses
2. **Memory Management**: Bedrock Memory stores last 5 conversation turns per session
3. **Session Tracking**: DynamoDB tracks user sessions with sanitized phone numbers as actor_id
4. **Asynchronous Messaging**: SQS decouples WhatsApp message sending from advisor handoff workflow
5. **Infrastructure as Code**: AWS CDK (TypeScript) for reproducible deployments
6. **Testing Strategy**: Property-based testing for correctness properties, integration tests for workflows

## User Journey Flow

1. Student visits landing page → fills inquiry form → submits
2. Form Submission Lambda creates Salesforce Lead with Status "New"
3. Chat interface opens with personalized greeting from Nemo
4. Student asks questions → Agent searches Knowledge Base → streams response with source attribution
5. After 4-6 meaningful exchanges, Nemo offers advisor connection
6. Student consents → provides timing preference → Advisor handoff workflow executes:
   - Search Salesforce for Lead by phone number
   - Update Lead Status from "New" to "Working"
   - Create Task with conversation summary and full transcript
   - Queue WhatsApp message to SQS
7. WhatsApp Lambda sends personalized message via Twilio
8. Message delivery status logged to DynamoDB

## Environment Variables

Each component requires specific environment variables. See `.env.example` files in:
- `Backend/admissions-ai-agent/.env.example` - CDK deployment credentials
- `Backend/admissions-ai-agent/AgentCore/.env.example` - Agent runtime configuration
- `Frontend/admissions-chat/.env.local.example` - Frontend API endpoints

## Development Guidelines

### Code Style
- **TypeScript**: Use strict mode, explicit types, functional components
- **Python**: Follow PEP 8, type hints required, async/await for I/O operations
- **Testing**: Write property-based tests for correctness properties (see design.md)

### Error Handling
- **Never expose technical details to users** - use friendly, actionable messages
- **Always log errors to CloudWatch** with structured format (timestamp, level, component, error_type)
- **Graceful degradation** - continue conversation when tools fail, retry with exponential backoff

### Agent Behavior
- **Personality**: Friendly, consultative, NOT robotic or overly formal
- **Conversation Flow**: Rapport building → exploration → knowledge sharing → advisor transition
- **Handoff Timing**: Offer advisor connection after 4-6 meaningful exchanges
- **Knowledge Base Usage**: Always cite sources with document names and URLs

## Project Structure

```
Claude-Code-Admissions-AI-Agent/
├── CLAUDE.md                          # This file - general project instructions
├── Backend/admissions-ai-agent/       # AWS infrastructure and Lambda functions
│   ├── CLAUDE.md                      # Infrastructure and CDK guidance
│   ├── lambda/
│   │   └── CLAUDE.md                  # Lambda development guidelines
│   └── AgentCore/
│       └── CLAUDE.md                  # Agent development and tools guidance
├── Frontend/admissions-chat/          # Next.js 15 application
│   ├── CLAUDE.md                      # Frontend development guidelines
│   └── src/components/
│       └── CLAUDE.md                  # Component development patterns
└── docs/                              # Reference documentation
    ├── architectureDeepDive.md
    ├── userGuide.md
    └── kiro docs/                     # Detailed design docs
        ├── design.md                  # Component interfaces, data models
        ├── requirements.md            # User stories and acceptance criteria
        └── tasks.md                   # Implementation plan with checkboxes
```

## Deployment Workflow

1. **Deploy Backend Infrastructure**: Run `Backend/admissions-ai-agent/deploy-scripts/deploy-backend.sh`
2. **Upload Knowledge Base Documents**: Upload to S3, sync Bedrock Knowledge Base
3. **Deploy Agent**: Run `Backend/admissions-ai-agent/AgentCore/scripts/launch_agent.sh`
4. **Deploy Frontend**: Build Next.js app, deploy to Amplify or Vercel
5. **Verify Integration**: Run end-to-end tests in `tests/integration/`

## Important Notes

- **AgentCore Configuration**: Run `agentcore configure` before first deployment
- **Memory ID**: Bedrock Memory ID is automatically created during agent configuration
- **Phone Number Format**: Always sanitize phone numbers (remove +, -, spaces) for actor_id
- **Session IDs**: Use UUIDs for unique session identification
- **CORS Configuration**: Ensure API Gateway and Lambda Function URLs allow frontend origin

## References

For detailed information, see:
- **Component Interfaces & Data Models**: `docs/kiro docs/design.md`
- **Requirements & Acceptance Criteria**: `docs/kiro docs/requirements.md`
- **Implementation Checklist**: `docs/kiro docs/tasks.md`
- **Architecture Diagram**: `docs/architectureDeepDive.md`
- **User Flow Screenshots**: `docs/userGuide.md`