"""
Advisor Handoff Tool

Orchestrates the complete handoff workflow from AI to human advisor.
Properties 17-27: Complete advisor handoff implementation
"""

import os
import logging
from typing import Dict, Any
from strands import tool

logger = logging.getLogger(__name__)

# Module-level context storage for handoff workflow
_handoff_context = {}


def set_context(phone_number: str, session_id: str, memory_id: str):
    """
    Set module-level context for handoff operations.

    This function stores context that's needed across multiple function calls
    during the handoff workflow.

    Args:
        phone_number: User's phone number
        session_id: Current session ID
        memory_id: Bedrock Memory ID for conversation history
    """
    global _handoff_context
    _handoff_context = {
        'phone_number': phone_number,
        'session_id': session_id,
        'memory_id': memory_id
    }
    logger.info(f"Set handoff context for phone {phone_number}, session {session_id}")


@tool
def complete_advisor_handoff(
    reason: str,
    student_name: str,
    timing_preference: str = "as soon as possible"
) -> Dict[str, Any]:
    """
    Complete the full advisor handoff workflow.

    This tool orchestrates the entire process of handing off a conversation
    from the AI agent to a human advisor. Use this when:
    - Student requests to speak with a human advisor
    - Complex question requires human expertise
    - Student has specific concerns that need personal attention

    Properties Implemented:
    - Property 17: User triggers handoff by requesting advisor
    - Property 18: "Hand off to advisor" indicator displayed
    - Property 19: History retrieved from Bedrock Memory
    - Property 20: Phone number used to search Salesforce
    - Property 21: Lead status updated to "Working"
    - Property 22: Task created with subject "Advisor Handoff: [Name]"
    - Property 23: Task Priority set to "High"
    - Property 24: Task Type set to "Advisor Handoff"
    - Property 25: Task Description includes full conversation transcript
    - Property 26: WhatsApp message queued to SQS
    - Property 27: Message includes timing preference

    Args:
        reason: Reason for handoff (e.g., "complex financial aid question")
        student_name: Student's full name
        timing_preference: When to contact - "as soon as possible", "2 hours",
                          "4 hours", or "tomorrow morning" (default: "as soon as possible")

    Returns:
        Confirmation message with handoff details
    """
    try:
        # Get context
        phone_number = _handoff_context.get('phone_number')
        session_id = _handoff_context.get('session_id')
        memory_id = _handoff_context.get('memory_id')

        if not phone_number or not session_id:
            logger.error("Handoff context not set")
            return {
                "status": "error",
                "content": [{
                    "text": "I encountered an issue initiating the handoff. Please contact admissions@university.edu directly."
                }]
            }

        logger.info(f"Starting advisor handoff for {student_name} (phone: {phone_number})")

        # Step 1: Retrieve full conversation history from Bedrock Memory
        # Property 19: History retrieved from Bedrock Memory
        from tools.session_utils import fetch_conversation_history

        conversation_history = fetch_conversation_history(
            session_id=session_id,
            phone_number=phone_number,
            memory_id=memory_id,
            max_turns=10  # Get more history for handoff
        )

        logger.info(f"Retrieved conversation history ({len(conversation_history)} chars)")

        # Step 2: Search Salesforce for Lead by phone number
        # Property 20: Phone number used to search Salesforce for Lead
        from tools.salesforce_tool import search_lead_by_phone

        lead_id, lead_data = search_lead_by_phone(phone_number)

        if not lead_id:
            logger.warning(f"No Lead found for phone {phone_number}")
            return {
                "status": "error",
                "content": [{
                    "text": f"I couldn't find your application in our system. Please contact admissions@university.edu with your phone number {phone_number} for assistance."
                }]
            }

        logger.info(f"Found Lead {lead_id} for phone {phone_number}")

        # Step 3: Update Lead status to "Working - Connected"
        # Property 21: Lead status updated to "Working - Connected"
        from tools.salesforce_tool import update_lead_status

        status_updated = update_lead_status(lead_id, status="Working - Connected")

        if not status_updated:
            logger.warning(f"Failed to update Lead status for {lead_id}")

        # Step 4: Create Task with full conversation history
        # Properties 22-25: Task created with specific attributes
        from tools.salesforce_tool import create_task_with_full_history

        task_description = f"Student requested advisor handoff.\n\nReason: {reason}\n\nTiming Preference: {timing_preference}"

        task_id = create_task_with_full_history(
            lead_id=lead_id,
            student_name=student_name,
            task_description=task_description,
            conversation_history=conversation_history
        )

        if not task_id:
            logger.error("Failed to create Task")
            return {
                "status": "error",
                "content": [{
                    "text": "I had trouble creating the handoff task. Please email admissions@university.edu directly."
                }]
            }

        logger.info(f"Created Task {task_id} for advisor handoff")

        # Step 5: Queue WhatsApp message via SQS
        # Properties 26-27: WhatsApp message queued with timing preference
        from tools.whatsapp_tool import send_whatsapp_message

        whatsapp_message = f"Hello {student_name}! A human advisor from our admissions team will contact you {timing_preference}. They have full context of our conversation and will help you with: {reason}"

        whatsapp_result = send_whatsapp_message(
            phone_number=phone_number,
            message=whatsapp_message,
            timing_preference=timing_preference,
            student_name=student_name
        )

        if whatsapp_result.get('status') != 'success':
            logger.warning("Failed to queue WhatsApp message")

        # Generate confirmation message
        timing_text = {
            "as soon as possible": "shortly",
            "2 hours": "in approximately 2 hours",
            "4 hours": "in approximately 4 hours",
            "tomorrow morning": "tomorrow morning"
        }.get(timing_preference.lower(), "soon")

        confirmation = f"""✓ **Handoff to Human Advisor Complete**

I've successfully connected you with our admissions team!

**What happens next:**
1. ✓ Your conversation has been saved and shared with an advisor
2. ✓ A high-priority task has been assigned (Task ID: {task_id[-6:]})
3. ✓ You'll receive a WhatsApp confirmation {timing_text}
4. ✓ An advisor will contact you {timing_text} to help with: {reason}

**Your application status:** Now under active review (Status: Working)

If you need immediate assistance, you can also email admissions@university.edu or call our admissions office.

Thank you for your interest in our university!"""

        return {
            "status": "success",
            "content": [{"text": confirmation}],
            "handoff_data": {
                "lead_id": lead_id,
                "task_id": task_id,
                "timing_preference": timing_preference,
                "student_name": student_name
            }
        }

    except Exception as e:
        logger.error(f"Error completing advisor handoff: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "content": [{
                "text": "I encountered an issue completing the handoff. Please contact admissions@university.edu directly for immediate assistance."
            }]
        }
