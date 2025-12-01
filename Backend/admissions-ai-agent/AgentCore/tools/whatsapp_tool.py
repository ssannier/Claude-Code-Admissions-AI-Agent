"""
WhatsApp Messaging Tool

Sends WhatsApp messages via SQS queue for asynchronous delivery.
Property 27: Agent schedules WhatsApp messages via SQS
"""

import os
import json
import logging
import uuid
from typing import Dict, Any
from datetime import datetime, timedelta
from strands import tool
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_sqs_client():
    """Get SQS client instance."""
    return boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'us-west-2'))


def calculate_delay_seconds(timing_preference: str) -> int:
    """
    Calculate SQS delay in seconds based on timing preference.

    Args:
        timing_preference: Student's timing preference

    Returns:
        Delay in seconds (max 900 for SQS)
    """
    preferences = {
        "as soon as possible": 0,
        "2 hours": 900,  # SQS max delay is 15 minutes, actual delay handled by scheduled events
        "4 hours": 900,
        "tomorrow morning": 900
    }
    return preferences.get(timing_preference.lower(), 0)


@tool
def send_whatsapp_message(
    phone_number: str,
    message: str,
    timing_preference: str = "as soon as possible",
    student_name: str = ""
) -> Dict[str, Any]:
    """Send a WhatsApp message to a student via SQS queue.

    This tool queues a WhatsApp message for delivery to the student.
    The message will be sent according to their timing preference.
    Use this when confirming actions, sending reminders, or providing
    information that needs to reach the student via WhatsApp.

    Property 27: Agent schedules WhatsApp messages via SQS

    Args:
        phone_number: Student's phone number in E.164 format (e.g., +15551234567)
        message: The message text to send (keep concise for WhatsApp)
        timing_preference: When to send - "as soon as possible", "2 hours",
                          "4 hours", or "tomorrow morning" (default: "as soon as possible")
        student_name: Student's name for logging purposes (optional)

    Returns:
        Confirmation that the message was queued successfully
    """
    try:
        # Validate phone number format
        if not phone_number.startswith('+'):
            phone_number = f"+{phone_number}"

        if len(phone_number) < 10:
            return {
                "status": "error",
                "content": [{"text": "Invalid phone number format. Please provide a valid phone number."}]
            }

        # Generate unique message ID
        eum_msg_id = str(uuid.uuid4())

        # Prepare SQS message
        message_body = {
            "phone_number": phone_number,
            "message": message,
            "timing_preference": timing_preference,
            "student_name": student_name,
            "eum_msg_id": eum_msg_id,
            "queued_at": datetime.utcnow().isoformat()
        }

        # Send to SQS
        sqs = get_sqs_client()
        queue_url = os.environ['WHATSAPP_QUEUE_URL']

        delay_seconds = calculate_delay_seconds(timing_preference)

        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            DelaySeconds=min(delay_seconds, 900),  # SQS max is 900 seconds (15 min)
            MessageAttributes={
                'Priority': {
                    'StringValue': 'high' if timing_preference == "as soon as possible" else 'normal',
                    'DataType': 'String'
                },
                'TimingPreference': {
                    'StringValue': timing_preference,
                    'DataType': 'String'
                }
            }
        )

        logger.info(f"Queued WhatsApp message {eum_msg_id} for {phone_number}, SQS MessageId: {response['MessageId']}")

        # Format user-friendly response
        timing_text = {
            "as soon as possible": "shortly",
            "2 hours": "in approximately 2 hours",
            "4 hours": "in approximately 4 hours",
            "tomorrow morning": "tomorrow morning"
        }.get(timing_preference.lower(), "soon")

        return {
            "status": "success",
            "content": [{
                "text": f"✓ WhatsApp message queued successfully. The student will receive it {timing_text} at {phone_number}."
            }],
            "message_id": eum_msg_id,
            "sqs_message_id": response['MessageId']
        }

    except KeyError as e:
        logger.error(f"Missing configuration: {str(e)}")
        return {
            "status": "error",
            "content": [{"text": "WhatsApp messaging is not configured. I'll create a task for manual outreach instead."}]
        }

    except ClientError as e:
        logger.error(f"SQS error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "content": [{"text": "Unable to queue WhatsApp message right now. Please try again or I can create a task for manual follow-up."}]
        }

    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "content": [{"text": "I encountered an issue sending the WhatsApp message. Let me create a task for our team to reach out manually."}]
        }
