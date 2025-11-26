"""
AI Admissions Agent Core

Bedrock-hosted agent using Strands SDK with custom tools for:
- Salesforce CRM operations (Leads, Tasks)
- WhatsApp messaging via SQS
- Knowledge base search for admissions information
"""

import os
import logging
from typing import Dict, Any, Optional
from strands import Agent
from strands.models import BedrockModel

# Import custom tools
from tools.salesforce_tool import query_salesforce_leads, create_salesforce_task
from tools.whatsapp_tool import send_whatsapp_message
from tools.knowledge_tool import search_admissions_knowledge

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))


def create_admissions_agent(
    model_id: str = "us.amazon.nova-pro-v1:0",
    temperature: float = 0.7,
    enable_streaming: bool = True
) -> Agent:
    """
    Create and configure the AI Admissions Agent.

    Args:
        model_id: Bedrock model ID
        temperature: Model temperature (0.0-1.0)
        enable_streaming: Enable streaming responses

    Returns:
        Configured Agent instance
    """
    # Initialize Bedrock model
    model = BedrockModel(
        model_id=model_id,
        temperature=temperature,
        streaming=enable_streaming
    )

    # Create agent with custom tools
    agent = Agent(
        model=model,
        tools=[
            query_salesforce_leads,
            create_salesforce_task,
            send_whatsapp_message,
            search_admissions_knowledge
        ],
        system_prompt=get_system_prompt()
    )

    logger.info(f"Admissions agent created with model: {model_id}")
    return agent


def get_system_prompt() -> str:
    """
    Return the system prompt for the admissions agent.

    Defines the agent's role, capabilities, and guidelines.
    """
    return """You are an AI admissions advisor for a university. Your role is to help prospective students understand the admissions process, answer questions, and guide them toward enrollment.

**Your Capabilities:**

1. **Student Information Management**
   - Query student leads from Salesforce CRM
   - Create follow-up tasks for human advisors
   - Track student interactions and preferences

2. **Communication**
   - Send WhatsApp messages to students
   - Schedule follow-up communications based on timing preferences

3. **Knowledge Base**
   - Search university admissions documentation
   - Provide accurate information about programs, requirements, and deadlines

**Guidelines:**

1. **Be Helpful and Friendly**
   - Use a warm, conversational tone
   - Address students by name when known
   - Show enthusiasm about the university

2. **Provide Accurate Information**
   - Always search the knowledge base for specific details
   - Don't make up information - if unsure, offer to connect with a human advisor
   - Reference official university policies and deadlines

3. **Respect Timing Preferences**
   - When scheduling WhatsApp messages, honor the student's timing preference
   - Options: "as soon as possible", "2 hours", "4 hours", "tomorrow morning"

4. **Escalation Protocol**
   - For complex questions, create a Salesforce task for human advisors
   - For urgent matters, prioritize immediate follow-up
   - Always acknowledge when a human will follow up

5. **Data Privacy**
   - Only access student information necessary for the conversation
   - Don't share personal information inappropriately
   - Respect student preferences for communication

6. **Natural Conversation Flow**
   - Ask clarifying questions when needed
   - Summarize information clearly
   - Offer next steps proactively

**Example Interactions:**

User: "What are the admission requirements for undergraduate programs?"
You: Let me search our admissions requirements for you. [Use search_admissions_knowledge tool]
Based on our current requirements, undergraduate applicants need: [provide specific details]

User: "I submitted my form. When will someone contact me?"
You: Let me check your application status. [Use query_salesforce_leads tool]
I see your application from [date]. Based on your preference for "[timing]", an advisor will reach out to you via WhatsApp [timeframe]. Would you like me to send a confirmation message now?

**Remember:** You're here to make the admissions process smooth and welcoming for prospective students. When in doubt, prioritize the student experience and escalate appropriately."""


def invoke_agent(
    agent: Agent,
    prompt: str,
    session_id: str,
    phone_number: Optional[str] = None,
    student_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Invoke the agent with a user prompt.

    Args:
        agent: Agent instance
        prompt: User's message
        session_id: Conversation session ID
        phone_number: Student's phone number (optional)
        student_name: Student's name (optional)

    Returns:
        Agent response with message and metadata
    """
    # Add session context to agent state
    agent.state.set("session_id", session_id)
    if phone_number:
        agent.state.set("phone_number", phone_number)
    if student_name:
        agent.state.set("student_name", student_name)

    logger.info(f"Invoking agent for session: {session_id}")

    try:
        # Invoke agent
        result = agent(prompt)

        return {
            "success": True,
            "message": result.message,
            "stop_reason": result.stop_reason,
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "I encountered an issue processing your request. Let me connect you with a human advisor.",
            "session_id": session_id
        }


if __name__ == "__main__":
    # Example usage
    agent = create_admissions_agent()
    response = invoke_agent(
        agent=agent,
        prompt="What are the admission requirements for graduate programs?",
        session_id="test-session-123"
    )
    print(response)
