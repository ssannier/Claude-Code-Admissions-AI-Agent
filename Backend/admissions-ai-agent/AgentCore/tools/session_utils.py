"""
Session Management Utilities

Provides utilities for session tracking, phone sanitization, and conversation history.
Property 16: Phone sanitization for actor IDs
Property 15: Conversation history retrieval
Properties 30-34: Session tracking in DynamoDB
"""

import os
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def sanitize_phone_for_actor_id(phone: str) -> str:
    """
    Sanitize phone number for use as Bedrock Memory actor ID.

    Property 16: Phone sanitization removes special characters

    Removes all non-numeric characters except leading '+' sign.
    Used as actor_id in Bedrock Memory for conversation tracking.

    Args:
        phone: Phone number in any format (e.g., "+1 (555) 123-4567")

    Returns:
        Sanitized phone in E.164 format (e.g., "+15551234567")

    Examples:
        >>> sanitize_phone_for_actor_id("+1 (555) 123-4567")
        '+15551234567'
        >>> sanitize_phone_for_actor_id("555-123-4567")
        '5551234567'
    """
    # Remove all characters except digits and leading +
    if phone.startswith('+'):
        sanitized = '+' + re.sub(r'[^0-9]', '', phone[1:])
    else:
        sanitized = re.sub(r'[^0-9]', '', phone)

    return sanitized


def fetch_conversation_history(
    session_id: str,
    phone_number: str,
    memory_id: str,
    max_turns: int = 5
) -> str:
    """
    Fetch conversation history from Bedrock Memory.

    Property 15: Agent retrieves last 5 conversation turns
    Properties 13-14: Messages stored in Bedrock Memory

    Retrieves up to max_turns recent conversation turns from Bedrock Memory
    and formats them for inclusion in agent context.

    Args:
        session_id: Session identifier for the conversation
        phone_number: User's phone number (used as actor_id)
        memory_id: Bedrock Memory identifier
        max_turns: Maximum number of conversation turns to retrieve (default: 5)

    Returns:
        Formatted conversation history string, or empty string if no history

    Example:
        >>> fetch_conversation_history("session-123", "+15551234567", "mem-456")
        "Previous conversation:\\nUser: What are requirements?\\nAssistant: For undergraduate..."
    """
    try:
        # Initialize Bedrock Agent Runtime client
        bedrock = boto3.client(
            'bedrock-agent-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )

        # Sanitize phone for actor ID
        actor_id = sanitize_phone_for_actor_id(phone_number)

        # Retrieve memory events
        response = bedrock.get_memory_events(
            memoryId=memory_id,
            sessionId=session_id,
            actorId=actor_id,
            maxResults=max_turns * 2  # Each turn = user + assistant message
        )

        events = response.get('memoryEvents', [])

        if not events:
            return ""

        # Format conversation history
        history_lines = ["Previous conversation:"]

        for event in events:
            event_type = event.get('eventType')
            content = event.get('content', {})

            if event_type == 'USER_INPUT':
                text = content.get('text', '')
                history_lines.append(f"User: {text}")
            elif event_type == 'ASSISTANT_RESPONSE':
                text = content.get('text', '')
                history_lines.append(f"Assistant: {text}")

        return "\n".join(history_lines)

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            logger.info(f"No memory found for session {session_id}, starting fresh conversation")
            return ""
        else:
            logger.error(f"Error fetching conversation history: {str(e)}", exc_info=True)
            return ""

    except Exception as e:
        logger.error(f"Unexpected error fetching history: {str(e)}", exc_info=True)
        return ""


def track_user_session(
    phone_number: str,
    session_id: str,
    student_name: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Track user session in DynamoDB.

    Properties 30-34: Session tracking in DynamoDB
    Property 30: Session ID is unique identifier
    Property 31: Session has phone number and student name
    Property 32: Session tracked in WhatsappSessions table
    Property 33: Session start time recorded
    Property 34: Session data accessible by phone number

    Creates or updates session record in DynamoDB WhatsappSessions table.

    Args:
        phone_number: User's phone number (partition key)
        session_id: Unique session identifier (sort key)
        student_name: Student's name (optional)
        additional_data: Additional session data to store (optional)

    Returns:
        True if successful, False otherwise
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        table_name = os.environ.get('WHATSAPP_SESSIONS_TABLE', 'WhatsappSessions')
        table = dynamodb.Table(table_name)

        # Sanitize phone number
        sanitized_phone = sanitize_phone_for_actor_id(phone_number)

        # Prepare session item
        item = {
            'phone_number': sanitized_phone,
            'session_id': session_id,
            'start_time': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'student_name': student_name or 'Unknown',
            'status': 'active'
        }

        # Add additional data if provided
        if additional_data:
            item.update(additional_data)

        # Store in DynamoDB
        table.put_item(Item=item)

        logger.info(f"Tracked session {session_id} for phone {sanitized_phone}")
        return True

    except Exception as e:
        logger.error(f"Error tracking session: {str(e)}", exc_info=True)
        return False


def update_session_activity(
    phone_number: str,
    session_id: str
) -> bool:
    """
    Update last activity timestamp for a session.

    Args:
        phone_number: User's phone number
        session_id: Session identifier

    Returns:
        True if successful, False otherwise
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        table_name = os.environ.get('WHATSAPP_SESSIONS_TABLE', 'WhatsappSessions')
        table = dynamodb.Table(table_name)

        sanitized_phone = sanitize_phone_for_actor_id(phone_number)

        table.update_item(
            Key={
                'phone_number': sanitized_phone,
                'session_id': session_id
            },
            UpdateExpression='SET last_activity = :timestamp',
            ExpressionAttributeValues={
                ':timestamp': datetime.utcnow().isoformat()
            }
        )

        return True

    except Exception as e:
        logger.error(f"Error updating session activity: {str(e)}", exc_info=True)
        return False


def get_active_sessions(phone_number: str) -> List[Dict[str, Any]]:
    """
    Retrieve all active sessions for a phone number.

    Args:
        phone_number: User's phone number

    Returns:
        List of active session records
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        table_name = os.environ.get('WHATSAPP_SESSIONS_TABLE', 'WhatsappSessions')
        table = dynamodb.Table(table_name)

        sanitized_phone = sanitize_phone_for_actor_id(phone_number)

        response = table.query(
            KeyConditionExpression='phone_number = :phone',
            FilterExpression='#status = :status',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':phone': sanitized_phone,
                ':status': 'active'
            }
        )

        return response.get('Items', [])

    except Exception as e:
        logger.error(f"Error retrieving sessions: {str(e)}", exc_info=True)
        return []
