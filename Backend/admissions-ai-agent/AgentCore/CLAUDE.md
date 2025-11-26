# AgentCore - AI Agent Development Guidelines

## Overview

This directory contains the Bedrock AgentCore agent ("Nemo") built with the Strands Agent SDK. The agent orchestrates conversations with prospective students, uses tools to search the knowledge base and coordinate advisor handoffs, and manages conversation history via Bedrock Memory.

**Agent Name**: Nemo
**Model**: Claude Sonnet 4.5 (global.anthropic.claude-sonnet-4-5-20250929-v1:0)
**Framework**: AWS Bedrock AgentCore with Strands Agent SDK

## Directory Structure

```
AgentCore/
├── CLAUDE.md                          # This file
├── nemo_agent.py                      # Main agent entrypoint
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── .bedrock_agentcore.yaml           # AgentCore config (generated)
├── Dockerfile                         # Container definition (generated)
├── .dockerignore                      # Docker ignore patterns
├── tools/                             # Agent tools
│   ├── __init__.py
│   ├── retrieve_tool.py               # Knowledge Base retrieval
│   ├── advisor_handoff_tool.py        # Advisor handoff orchestration
│   ├── session_utils.py               # Session tracking utilities
│   ├── salesforce_helpers.py          # Salesforce integration
│   └── whatsapp_helpers.py            # WhatsApp messaging
├── prompts/                           # System prompts
│   └── system_prompt.txt              # Nemo personality and instructions
├── scripts/                           # Deployment scripts
│   └── launch_agent.sh                # AgentCore launch script
└── tests/                             # Agent tests
    ├── test_agent.py
    ├── test_tools.py
    ├── test_session_utils.py
    └── test_properties.py             # Property-based tests
```

## Agent Architecture

### Flow Diagram

```
Frontend → Agent Proxy Lambda → Bedrock AgentCore (Nemo)
                                       ↓
                    ┌──────────────────┼──────────────────┐
                    ↓                  ↓                  ↓
           DynamoDB Sessions   Bedrock Memory   Knowledge Base
                    ↓                  ↓                  ↓
               Track session    Store messages    Search docs

                    ↓ (on advisor handoff)

          Salesforce Update + Task Creation
                    ↓
              SQS Queue → WhatsApp Lambda
```

### Agent Entrypoint

```python
# nemo_agent.py
import os
from strands_agents import Agent, BedrockModel
from bedrock_agentcore import app
from tools.retrieve_tool import retrieve_university_info
from tools.advisor_handoff_tool import complete_advisor_handoff, set_context
from tools.session_utils import (
    sanitize_phone_for_actor_id,
    fetch_conversation_history,
    track_user_session
)

# Initialize agent
model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region=os.getenv("AWS_REGION", "us-east-1")
)

with open("prompts/system_prompt.txt", "r") as f:
    system_prompt = f.read()

agent = Agent(
    name="Nemo",
    model=model,
    system_prompt=system_prompt,
    tools=[retrieve_university_info, complete_advisor_handoff]
)

@app.entrypoint
async def strands_agent_bedrock(payload):
    """
    Main agent entrypoint invoked by Bedrock AgentCore.

    Args:
        payload: {
            prompt: str,
            session_id: str,
            phone_number: str,
            system_message?: str  # Optional form context
        }

    Yields:
        Event dicts: {response}, {thinking}, {tool_result}, {final_result}, {error}
    """
    prompt = payload.get("prompt")
    session_id = payload.get("session_id")
    phone_number = payload.get("phone_number")
    system_message = payload.get("system_message", "")

    try:
        # 1. Track session in DynamoDB
        track_user_session(phone_number, session_id)

        # 2. Retrieve conversation history from Bedrock Memory
        actor_id = sanitize_phone_for_actor_id(phone_number)
        max_turns = int(os.getenv("MAX_HISTORY_TURNS", "5"))
        memory_id = os.getenv("AGENTCORE_MEMORY_ID")

        history = fetch_conversation_history(
            session_id=session_id,
            phone_number=phone_number,
            memory_id=memory_id,
            max_turns=max_turns
        )

        # 3. Store user message in Bedrock Memory
        store_message_in_memory(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            content=prompt,
            role="user"
        )

        # 4. Set context for tools (phone_number, session_id)
        set_context(phone_number=phone_number, session_id=session_id)

        # 5. Enhance prompt with history and system message
        enhanced_prompt = f"{system_message}\n\nConversation History:\n{history}\n\nUser: {prompt}"

        # 6. Stream agent response
        async for event in agent.run(enhanced_prompt, stream=True):
            if event.type == "response":
                yield {"response": event.content}
            elif event.type == "thinking":
                yield {"thinking": event.content}
            elif event.type == "tool_result":
                yield {"tool_result": event.content}
            elif event.type == "final":
                # 7. Store assistant response in Bedrock Memory
                store_message_in_memory(
                    memory_id=memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                    content=event.content,
                    role="assistant"
                )
                yield {"final_result": event.content}

    except Exception as e:
        logging.error(f"Agent error: {str(e)}", exc_info=True)
        yield {"error": "I'm having trouble right now. Please try again."}


def store_message_in_memory(memory_id, actor_id, session_id, content, role):
    """Store message in Bedrock Memory."""
    import boto3
    client = boto3.client('bedrock-agent-runtime')

    client.put_memory_events(
        memoryId=memory_id,
        actorId=actor_id,
        sessionId=session_id,
        events=[{
            'type': 'MESSAGE',
            'content': content,
            'role': role,
            'timestamp': datetime.utcnow().isoformat()
        }]
    )
```

## System Prompt Guidelines

### Nemo's Personality
- **Friendly and consultative**: NOT robotic or overly formal
- **Empathetic**: Understands the stress of choosing a university
- **Knowledgeable**: Expert on the university's programs
- **Patient**: Willing to answer multiple questions
- **Professional**: Maintains boundaries, redirects off-topic questions

### Conversation Flow Phases

**Phase 1: Rapport Building (1-2 exchanges)**
- Greet student by first name
- Acknowledge their interest in the university
- Ask open-ended questions about their goals

**Phase 2: Exploration (2-3 exchanges)**
- Listen actively to student concerns and interests
- Ask clarifying questions
- Identify relevant programs and information

**Phase 3: Knowledge Sharing (2-4 exchanges)**
- Use `retrieve_university_info` tool to search knowledge base
- Provide detailed, accurate information with source citations
- Answer follow-up questions

**Phase 4: Advisor Transition (1-2 exchanges)**
- After 4-6 meaningful exchanges, offer human advisor connection
- Explain benefits: personalized guidance, application support
- If student consents, ask for timing preference
- Execute `complete_advisor_handoff` tool

### System Prompt Template

```txt
# prompts/system_prompt.txt

You are Nemo, a friendly and knowledgeable AI assistant for {UNIVERSITY_NAME}. Your role is to help prospective students explore academic programs, understand admissions requirements, and learn about campus life through natural conversation.

## Your Personality
- Friendly and approachable, NOT robotic or overly formal
- Empathetic to the stress of choosing a university
- Expert on {UNIVERSITY_NAME} programs and admissions
- Patient and willing to answer multiple questions
- Professional but warm

## Conversation Guidelines

### Knowledge Base Usage
- When students ask factual questions, use the `retrieve_university_info` tool to search the knowledge base
- Always cite sources: mention document names and provide URLs
- If information isn't in the knowledge base, acknowledge this honestly

### Advisor Handoff
- After 4-6 meaningful message exchanges, offer to connect the student with a human enrollment advisor
- Explain benefits: personalized guidance, application support, program recommendations
- If student consents, ask for timing preference: "within 2 hours" or "during business hours tomorrow"
- Use the `complete_advisor_handoff` tool with:
  - conversation_summary: 2-3 sentence summary of discussion
  - whatsapp_message: Personalized message matching timing preference
  - programs: Comma-separated list of programs discussed
  - concerns: Student's main questions or concerns

### Important Rules
- NEVER make up information - only use knowledge base results
- NEVER promise admission or make guarantees about acceptance
- NEVER discuss pricing or financial aid without knowledge base confirmation
- ALWAYS be respectful of all backgrounds and identities
- If asked off-topic questions, politely redirect to university-related topics

## Example Exchanges

User: "Hi, I'm interested in engineering programs."
Nemo: "Hi [FirstName]! It's great to hear you're interested in engineering at {UNIVERSITY_SHORT_NAME}. We have several excellent engineering programs. To help me point you in the right direction, what area of engineering are you most excited about? For example, mechanical, electrical, computer, or civil?"

User: "I'm thinking about computer engineering. What's the curriculum like?"
Nemo: "Great choice! Let me look up the details about our Computer Engineering program for you."
[Uses retrieve_university_info tool]
Nemo: "Our Computer Engineering program combines hardware and software, covering areas like embedded systems, computer architecture, and digital signal processing. [Provides specific details from knowledge base]. You can read more in the Program Catalog (link). What aspect of computer engineering interests you most?"

[After 5-6 exchanges]
Nemo: "I can tell you're serious about exploring {UNIVERSITY_SHORT_NAME}'s Computer Engineering program! Would you like me to connect you with one of our enrollment advisors? They can provide personalized guidance on the application process, discuss your specific background, and answer any detailed questions. What do you think?"

User: "Yes, that would be helpful."
Nemo: "Excellent! When would you prefer to be contacted via WhatsApp? I can arrange for an advisor to reach out within the next 2 hours, or during business hours tomorrow if that works better."

User: "Within 2 hours would be great."
Nemo: [Executes complete_advisor_handoff tool]
"Perfect! I've connected you with our enrollment team. You'll receive a WhatsApp message within the next 2 hours to schedule a conversation with an advisor who specializes in engineering programs. They'll have access to our chat history, so you won't need to repeat anything. Is there anything else I can help you with in the meantime?"
```

## Tool Development

### 1. Knowledge Base Retrieval Tool

```python
# tools/retrieve_tool.py
import os
import boto3
from strands_agents import tool
import logging

logger = logging.getLogger(__name__)

@tool
def retrieve_university_info(
    text: str,
    numberOfResults: int = 5,
    score: float = 0.5
) -> str:
    """
    Search the university knowledge base for relevant information.

    Args:
        text: Query text describing what to search for
        numberOfResults: Maximum number of results to return (default: 5)
        score: Minimum relevance score threshold 0-1 (default: 0.5)

    Returns:
        Formatted string with search results and source attribution
    """
    try:
        client = boto3.client('bedrock-agent-runtime', region_name=os.getenv('AWS_REGION'))
        kb_id = os.getenv('ENGLISH_KNOWLEDGE_BASE_ID')

        response = client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': text},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': numberOfResults,
                    'overrideSearchType': 'HYBRID'
                }
            }
        )

        results = []
        for result in response['retrievalResults']:
            relevance_score = result['score']

            # Filter by score threshold (Property 9)
            if relevance_score >= score:
                content = result['content']['text']
                location = result['location']

                # Extract source attribution (Property 10)
                source_uri = location.get('s3Location', {}).get('uri', 'Unknown')
                doc_name = source_uri.split('/')[-1] if source_uri != 'Unknown' else 'Unknown'

                metadata = result.get('metadata', {})
                doc_url = metadata.get('x-amz-bedrock-kb-source-uri', '')

                results.append({
                    'content': content,
                    'score': relevance_score,
                    'source': doc_name,
                    'url': doc_url
                })

        if not results:
            return "No relevant information found in the knowledge base. Please try rephrasing your question."

        # Format results with source attribution
        formatted = "Based on the knowledge base:\n\n"
        for idx, result in enumerate(results, 1):
            formatted += f"{idx}. {result['content']}\n"
            formatted += f"   Source: {result['source']}"
            if result['url']:
                formatted += f" ({result['url']})"
            formatted += f" (Relevance: {result['score']:.2f})\n\n"

        return formatted

    except Exception as e:
        logger.error(f"Knowledge base retrieval error: {str(e)}", exc_info=True)
        return "I'm having trouble accessing the knowledge base right now. Let me try to help you in another way."
```

### 2. Advisor Handoff Tool

```python
# tools/advisor_handoff_tool.py
import os
import boto3
from strands_agents import tool
from tools.salesforce_helpers import (
    search_lead_by_phone,
    update_lead_status,
    create_task_with_full_history
)
from tools.whatsapp_helpers import queue_whatsapp_message
from tools.session_utils import fetch_conversation_history, sanitize_phone_for_actor_id
import logging

logger = logging.getLogger(__name__)

# Module-level context storage
_context = {}

def set_context(phone_number: str, session_id: str):
    """Set context for tool to access phone_number and session_id."""
    _context['phone_number'] = phone_number
    _context['session_id'] = session_id

@tool
def complete_advisor_handoff(
    conversation_summary: str,
    whatsapp_message: str,
    programs: str,
    concerns: str
) -> str:
    """
    Complete the advisor handoff workflow: update Salesforce, create Task, queue WhatsApp.

    Args:
        conversation_summary: 2-3 sentence summary of the conversation
        whatsapp_message: Personalized WhatsApp message matching timing preference
        programs: Comma-separated list of programs discussed
        concerns: Student's main questions or concerns

    Returns:
        Success or error message
    """
    try:
        phone_number = _context.get('phone_number')
        session_id = _context.get('session_id')

        if not phone_number or not session_id:
            return "Error: Missing context information."

        # 1. Retrieve full conversation history from Bedrock Memory
        memory_id = os.getenv('AGENTCORE_MEMORY_ID')
        actor_id = sanitize_phone_for_actor_id(phone_number)

        full_transcript = fetch_conversation_history(
            session_id=session_id,
            phone_number=phone_number,
            memory_id=memory_id,
            max_turns=50  # Get full conversation
        )

        # 2. Search Salesforce for Lead by phone (Property 20)
        lead_id, lead_data = search_lead_by_phone(phone_number)

        if not lead_id:
            return "I couldn't find your contact information in our system. Please make sure you submitted the inquiry form first."

        # 3. Update Lead status to "Working" (Property 21)
        update_lead_status(lead_id, status="Working - Connected")

        # 4. Create Task with summary and transcript (Properties 22-25)
        student_name = f"{lead_data['FirstName']} {lead_data['LastName']}"

        task_description = f"""
**Conversation Summary:**
{conversation_summary}

**Programs Discussed:**
{programs}

**Student Concerns:**
{concerns}

**Full Chat Transcript:**
{full_transcript}
"""

        create_task_with_full_history(
            lead_id=lead_id,
            student_name=student_name,
            task_description=task_description
        )

        # 5. Queue WhatsApp message (Properties 26-27)
        import uuid
        eum_msg_id = str(uuid.uuid4())

        queue_whatsapp_message(
            phone_number=phone_number,
            message=whatsapp_message,
            timing_preference="2 hours",  # Extract from whatsapp_message
            student_name=student_name,
            eum_msg_id=eum_msg_id
        )

        logger.info(f"Advisor handoff completed for {student_name}, Lead ID: {lead_id}")

        return f"Perfect! I've connected you with our enrollment team. You'll receive a WhatsApp message shortly."

    except Exception as e:
        logger.error(f"Advisor handoff error: {str(e)}", exc_info=True)
        return "I encountered an issue coordinating the handoff. Please try again or contact admissions directly."
```

### 3. Session Utilities

```python
# tools/session_utils.py
import os
import boto3
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
dynamodb = boto3.resource('dynamodb')
bedrock_client = boto3.client('bedrock-agent-runtime')

def sanitize_phone_for_actor_id(phone: str) -> str:
    """
    Remove +, -, and spaces from phone number for use as actor_id.

    Property 16: Phone number sanitization removes special characters
    """
    return re.sub(r'[+\-\s]', '', phone)

def fetch_conversation_history(
    session_id: str,
    phone_number: str,
    memory_id: str,
    max_turns: int
) -> str:
    """
    Retrieve last N conversation turns from Bedrock Memory.

    Property 15: Agent retrieves last 5 conversation turns
    """
    try:
        actor_id = sanitize_phone_for_actor_id(phone_number)

        response = bedrock_client.list_memory_events(
            memoryId=memory_id,
            actorId=actor_id,
            sessionId=session_id,
            maxResults=max_turns * 2  # 2 messages per turn (user + assistant)
        )

        events = response.get('memoryEvents', [])

        # Format as conversation history
        history = []
        for event in events:
            role = event['role']
            content = event['content']
            role_label = "User" if role == "user" else "Assistant"
            history.append(f"{role_label}: {content}")

        return "\n".join(history)

    except Exception as e:
        logger.error(f"Error fetching conversation history: {str(e)}")
        return ""

def track_user_session(phone_number: str, session_id: str):
    """
    Track user session in DynamoDB WhatsappSessions table.

    Properties 30-33: Session tracking
    """
    try:
        table = dynamodb.Table(os.getenv('SESSIONS_TABLE_NAME'))

        # Check for existing record (Property 30)
        response = table.get_item(Key={'phone_number': phone_number})

        now = datetime.utcnow()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        if 'Item' in response:
            # Update existing record (Property 31)
            existing = response['Item']
            sessions = existing.get('sessions', [])
            sessions.append(session_id)

            table.update_item(
                Key={'phone_number': phone_number},
                UpdateExpression='SET sessions = :s, latest_session_id = :l, web_app_last_connect_date = :d, web_app_last_connect_time = :t',
                ExpressionAttributeValues={
                    ':s': sessions,
                    ':l': session_id,
                    ':d': date_str,
                    ':t': time_str
                }
            )
        else:
            # Create new record (Property 32)
            table.put_item(
                Item={
                    'phone_number': phone_number,
                    'sessions': [session_id],
                    'latest_session_id': session_id,
                    'web_app_last_connect_date': date_str,
                    'web_app_last_connect_time': time_str
                }
            )

        logger.info(f"Tracked session {session_id} for {phone_number}")

    except Exception as e:
        logger.error(f"Error tracking session: {str(e)}", exc_info=True)
```

## Environment Variables

```bash
# .env.example

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Bedrock AgentCore
AGENTCORE_MEMORY_ID=your-memory-id  # Created during agentcore configure
MAX_HISTORY_TURNS=5                 # Number of conversation turns to retrieve

# Knowledge Base
ENGLISH_KNOWLEDGE_BASE_ID=your-kb-id

# DynamoDB Tables
SESSIONS_TABLE_NAME=WhatsappSessions
MESSAGE_TRACKING_TABLE=WhatsAppMessageTracking

# SQS Queue
TWILIO_WHATSAPP_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/twilio-whatsapp-queue

# Salesforce Credentials
SF_USERNAME=your-salesforce-username
SF_PASSWORD=your-salesforce-password
SF_TOKEN=your-salesforce-security-token

# Twilio Credentials
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+15551234567

# University Branding
UNIVERSITY_NAME=Your University Name
UNIVERSITY_SHORT_NAME=YUN

# Logging
LOG_LEVEL=INFO
```

## Deployment Process

### 1. Configure AgentCore

```bash
cd Backend/admissions-ai-agent/AgentCore

# Run agentcore configure
agentcore configure

# Provide inputs:
# - Execution role ARN: (from CDK stack output)
# - ECR repository URI: (from CDK stack output)
# - Enable short-term memory: yes
# - Memory retention: 7 days

# This generates:
# - .bedrock_agentcore.yaml
# - Dockerfile
# - .dockerignore
```

### 2. Create Launch Script

```bash
# scripts/launch_agent.sh
#!/bin/bash

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Launch agent with all environment variables
agentcore launch \
    --env AWS_REGION=$AWS_REGION \
    --env AGENTCORE_MEMORY_ID=$AGENTCORE_MEMORY_ID \
    --env MAX_HISTORY_TURNS=$MAX_HISTORY_TURNS \
    --env ENGLISH_KNOWLEDGE_BASE_ID=$ENGLISH_KNOWLEDGE_BASE_ID \
    --env SESSIONS_TABLE_NAME=$SESSIONS_TABLE_NAME \
    --env MESSAGE_TRACKING_TABLE=$MESSAGE_TRACKING_TABLE \
    --env TWILIO_WHATSAPP_QUEUE_URL=$TWILIO_WHATSAPP_QUEUE_URL \
    --env SF_USERNAME=$SF_USERNAME \
    --env SF_PASSWORD=$SF_PASSWORD \
    --env SF_TOKEN=$SF_TOKEN \
    --env TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID \
    --env TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN \
    --env TWILIO_PHONE_NUMBER=$TWILIO_PHONE_NUMBER \
    --env UNIVERSITY_NAME="$UNIVERSITY_NAME" \
    --env UNIVERSITY_SHORT_NAME=$UNIVERSITY_SHORT_NAME \
    --env LOG_LEVEL=$LOG_LEVEL

echo "Agent launched successfully!"
echo "Agent Runtime ARN: (copy from output)"
```

### 3. Deploy Agent

```bash
chmod +x scripts/launch_agent.sh
./scripts/launch_agent.sh

# This will:
# 1. Build Docker image
# 2. Push to ECR
# 3. Deploy to Bedrock AgentCore
# 4. Output Agent Runtime ARN

# Save the Agent Runtime ARN - you'll need it for the CDK stack
```

### 4. Update CDK Stack with Agent ARN

```bash
# Update Backend/admissions-ai-agent/.env with:
AGENT_RUNTIME_ARN=arn:aws:bedrock:us-east-1:123456789012:agent-runtime/xyz

# Redeploy CDK stack
cd Backend/admissions-ai-agent
npx cdk deploy
```

## Testing Strategy

### Unit Tests

```python
# tests/test_tools.py
import pytest
from tools.retrieve_tool import retrieve_university_info
from tools.session_utils import sanitize_phone_for_actor_id

def test_phone_sanitization():
    assert sanitize_phone_for_actor_id("+1-555-123-4567") == "15551234567"
    assert sanitize_phone_for_actor_id("+1 555 123 4567") == "15551234567"

def test_knowledge_base_retrieval():
    # Mock Bedrock client
    result = retrieve_university_info("computer engineering program")
    assert "Source:" in result
    assert "Relevance:" in result
```

### Property-Based Tests

```python
# tests/test_properties.py
from hypothesis import given, strategies as st

# Feature: ai-admissions-agent, Property 16: Phone number sanitization removes special characters
@given(phone=st.text(min_size=10))
def test_phone_sanitization_removes_special_chars(phone):
    """Phone sanitization should remove all +, -, and space characters."""
    result = sanitize_phone_for_actor_id(phone)
    assert '+' not in result
    assert '-' not in result
    assert ' ' not in result

# Feature: ai-admissions-agent, Property 9: Knowledge base results filtered by score threshold
@given(score=st.floats(min_value=0.0, max_value=1.0))
def test_knowledge_base_filters_by_score(score):
    """Only results with score >= threshold should be included."""
    # Test implementation
    pass
```

## Monitoring & Debugging

### CloudWatch Logs

Agent logs appear in CloudWatch Logs:
- Log group: `/aws/bedrock/agentcore/{agent-id}`
- Search for: `ERROR`, `WARNING`, session IDs, phone numbers

### Bedrock AgentCore Observability

Access observability dashboard:
1. AWS Console → Bedrock → AgentCore
2. Select your agent
3. View metrics: invocations, latency, errors
4. View traces: tool usage, response times

### Common Issues

**Issue: Tool not being called**
- Check system prompt clearly describes when to use tool
- Verify tool parameters are well-documented
- Review agent logs for reasoning

**Issue: Memory not persisting**
- Verify Memory ID is correct
- Check IAM permissions for bedrock:PutMemory
- Ensure actor_id and session_id are consistent

**Issue: Knowledge Base returns no results**
- Verify Knowledge Base ID is correct
- Check documents are synced in Bedrock console
- Lower score threshold (0.3 instead of 0.5)

## Related Documentation

- **Infrastructure**: See `../CLAUDE.md` for CDK stack and IAM permissions
- **Lambda Integration**: See `../lambda/CLAUDE.md` for Agent Proxy Lambda
- **Requirements**: See `docs/kiro docs/requirements.md` for agent requirements
- **Data Models**: See `docs/kiro docs/design.md` for payload and event schemas
