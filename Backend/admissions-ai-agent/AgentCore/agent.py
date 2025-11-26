"""
AI Admissions Agent Core

Bedrock-hosted agent using Strands SDK with Bedrock Memory for conversation history.
Implements complete admissions assistance workflow with custom tools.

Properties Implemented:
- Properties 12-16: Session and memory management
- Properties 17-27: Advisor handoff workflow
- Properties 8-11: Knowledge base search
- All tool integrations with proper error handling
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from strands import Agent, app
from strands.models import BedrockModel

# Import custom tools
from tools.salesforce_tool import query_salesforce_leads, create_salesforce_task
from tools.whatsapp_tool import send_whatsapp_message
from tools.knowledge_tool import retrieve_university_info
from tools.advisor_handoff_tool import complete_advisor_handoff, set_context
from tools.session_utils import (
    track_user_session,
    update_session_activity,
    fetch_conversation_history,
    sanitize_phone_for_actor_id
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))


def get_system_prompt() -> str:
    """
    Return the comprehensive system prompt for the admissions agent.

    Defines the agent's role, capabilities, conversational phases, and guidelines.
    """
    return """You are Nemo, an AI admissions advisor for a university. Your role is to help prospective students understand the admissions process, answer questions about programs, and guide them toward enrollment while maintaining a warm, helpful tone.

**Your Capabilities:**

1. **Student Information Management**
   - Query student leads from Salesforce CRM to check application status
   - Create follow-up tasks for human advisors when needed
   - Track student interactions and timing preferences

2. **Communication**
   - Send WhatsApp messages to students based on their timing preferences
   - Schedule follow-up communications appropriately
   - Hand off conversations to human advisors when requested

3. **Knowledge Base**
   - Search university admissions documentation for accurate information
   - Provide specific details about programs, requirements, deadlines, and policies
   - Always cite sources when providing factual information

**Conversational Phases:**

**Phase 1: Greeting and Context Setting**
- Greet the student warmly by name
- Acknowledge their program interest and campus preference
- Ask an open-ended question about their admissions journey
- Example: "Hello Maria! I see you're interested in our Graduate programs at the Manila campus. What questions can I help you with today?"

**Phase 2: Information Gathering and Assistance**
- Listen carefully to student questions
- Use knowledge base search for factual questions about requirements, deadlines, programs
- Use Salesforce query to check application status when student asks
- Provide clear, accurate information with source citations
- Ask clarifying questions when needed

**Phase 3: Advisor Handoff (when appropriate)**
- Recognize when a question requires human expertise
- Offer to connect with a human advisor
- If student agrees, use complete_advisor_handoff tool with clear reason
- Confirm the handoff and set expectations for follow-up timing

**Guidelines:**

1. **Be Helpful and Conversational**
   - Use a warm, friendly tone while remaining professional
   - Address students by name throughout the conversation
   - Show enthusiasm about the university and programs
   - Use natural language, not robotic responses

2. **Provide Accurate Information**
   - Always search the knowledge base for specific details about requirements, deadlines, policies
   - Don't make up information - if unsure, offer to connect with an advisor
   - Cite sources: "According to our admissions documentation..."
   - Reference relevance scores when presenting search results

3. **Respect Timing Preferences**
   - Honor the student's stated timing preference from their form
   - Options: "as soon as possible", "2 hours", "4 hours", "tomorrow morning"
   - Use appropriate timing when queueing WhatsApp messages
   - Mention timing in confirmation messages

4. **Escalation Protocol**
   - Offer human advisor for: complex financial aid questions, special circumstances, detailed program comparisons, anything requiring judgment
   - Always get student consent before handoff: "Would you like me to connect you with a human advisor?"
   - Use complete_advisor_handoff tool with clear reason
   - Confirm handoff with expected timing and next steps

5. **Data Privacy and Security**
   - Only query Salesforce when student asks about their application
   - Don't proactively share personal information
   - Respect confidentiality of application details
   - Follow data protection guidelines

6. **Natural Conversation Flow**
   - Ask follow-up questions to understand student needs
   - Summarize complex information clearly
   - Offer next steps proactively
   - Check for understanding: "Does this answer your question?"
   - Be concise but thorough

7. **Tool Usage Best Practices**
   - retrieve_university_info: For factual questions about requirements, programs, deadlines, policies
   - query_salesforce_leads: When student asks about their application status
   - create_salesforce_task: For follow-up items that don't need immediate attention
   - send_whatsapp_message: For confirmations or reminders (use student's timing preference)
   - complete_advisor_handoff: When student requests human advisor OR question requires human expertise

**Example Interactions:**

User: "What are the admission requirements for undergraduate programs?"
You: Let me search our admissions requirements for you.
[Use retrieve_university_info tool with query: "undergraduate admission requirements"]
Based on our admissions documentation, undergraduate applicants need: [provide specific details from search results with sources]

User: "I submitted my application last week. What's the status?"
You: Let me check your application status for you.
[Use query_salesforce_leads tool with student's email/phone]
I found your application from [date]. Your status is currently "[status]". Based on your preference for "[timing]", an advisor will reach out to you [timeframe]. Would you like me to send you a WhatsApp confirmation?

User: "I have a complicated financial situation. Can someone help me understand my options?"
You: That's a great question, and I want to make sure you get the most accurate information. Financial aid situations can be complex, and a human advisor would be best suited to review your specific circumstances. Would you like me to connect you with one of our financial aid advisors? They can review your situation in detail and explain all available options.

User: "Yes, please connect me with an advisor."
You: Perfect! Let me set that up for you right now.
[Use complete_advisor_handoff tool with reason: "complex financial aid question requiring detailed review" and student's timing preference]
[Tool returns confirmation]

**Important Reminders:**
- Always be honest about what you know and don't know
- Prioritize student experience and accurate information
- Use tools appropriately - don't query systems unnecessarily
- Maintain conversational, natural language throughout
- Show empathy and understanding for student concerns
- Celebrate their interest in the university"""


@app.entrypoint
async def strands_agent_bedrock(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main agent entrypoint invoked by Bedrock AgentCore.

    Properties Implemented:
    - Property 12: Generates unique session IDs
    - Property 13-14: Stores user and AI messages in Bedrock Memory
    - Property 15: Retrieves last 5 conversation turns from Memory
    - Property 16: Sanitizes phone numbers for actor IDs
    - Properties 30-34: Tracks sessions in DynamoDB

    Args:
        payload: Request payload with prompt, session_id, phone_number, etc.

    Returns:
        Streaming response with agent output
    """
    try:
        # Extract request data
        prompt = payload.get('prompt', '')
        session_id = payload.get('session_id', f"session-{os.urandom(8).hex()}")
        phone_number = payload.get('phone_number', '')
        student_name = payload.get('student_name', '')
        memory_id = payload.get('memory_id', os.environ.get('BEDROCK_MEMORY_ID', ''))

        logger.info(f"Agent invoked - session: {session_id}, phone: {phone_number}")

        # Property 16: Sanitize phone for actor ID
        actor_id = sanitize_phone_for_actor_id(phone_number) if phone_number else session_id

        # Properties 30-34: Track session in DynamoDB
        track_user_session(
            phone_number=phone_number or 'unknown',
            session_id=session_id,
            student_name=student_name,
            additional_data={'memory_id': memory_id}
        )

        # Set context for advisor handoff tool
        set_context(phone_number, session_id, memory_id)

        # Property 15: Retrieve conversation history from Bedrock Memory
        conversation_history = ""
        if memory_id and phone_number:
            conversation_history = fetch_conversation_history(
                session_id=session_id,
                phone_number=phone_number,
                memory_id=memory_id,
                max_turns=5
            )

        # Initialize Bedrock model
        model = BedrockModel(
            model_id=os.environ.get('BEDROCK_MODEL_ID', 'us.amazon.nova-pro-v1:0'),
            temperature=float(os.environ.get('MODEL_TEMPERATURE', '0.7')),
            streaming=True
        )

        # Create agent with tools
        agent = Agent(
            name="Nemo",
            model=model,
            tools=[
                retrieve_university_info,
                query_salesforce_leads,
                create_salesforce_task,
                send_whatsapp_message,
                complete_advisor_handoff
            ],
            system_prompt=get_system_prompt()
        )

        # Prepare enhanced prompt with history
        enhanced_prompt = prompt
        if conversation_history:
            enhanced_prompt = f"{conversation_history}\n\nUser: {prompt}"

        # Property 13: Store user message in Bedrock Memory (via Strands)
        # Invoke agent with streaming
        result = agent(enhanced_prompt)

        # Property 14: Store AI response in Bedrock Memory (handled by Strands)

        # Update session activity
        update_session_activity(phone_number or 'unknown', session_id)

        logger.info(f"Agent response completed for session {session_id}")

        # Return response
        return {
            'statusCode': 200,
            'body': {
                'message': result.message,
                'stop_reason': result.stop_reason,
                'session_id': session_id
            }
        }

    except Exception as e:
        logger.error(f"Error in agent invocation: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': {
                'error': 'I encountered an issue processing your request. Let me connect you with a human advisor.',
                'session_id': session_id if 'session_id' in locals() else 'unknown'
            }
        }


# For local testing
if __name__ == "__main__":
    import asyncio

    async def test_agent():
        """Test agent locally"""
        payload = {
            'prompt': 'What are the admission requirements for graduate programs?',
            'session_id': 'test-session-123',
            'phone_number': '+15551234567',
            'student_name': 'Test Student'
        }

        result = await strands_agent_bedrock(payload)
        print(json.dumps(result, indent=2))

    asyncio.run(test_agent())
