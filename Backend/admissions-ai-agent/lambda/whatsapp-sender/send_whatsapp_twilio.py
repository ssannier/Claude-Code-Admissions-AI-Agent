"""
WhatsApp Sender Lambda Handler

Processes SQS messages and sends WhatsApp messages via Twilio.
Logs delivery status to DynamoDB.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))


def send_whatsapp_message(
    phone_number: str,
    message_text: str,
    twilio_client,
    twilio_phone: str
) -> Dict[str, Any]:
    """
    Send WhatsApp message via Twilio.

    Property 28: WhatsApp Lambda sends via Twilio

    Args:
        phone_number: Recipient phone number (E.164 format)
        message_text: Message content
        twilio_client: Twilio client instance
        twilio_phone: Twilio WhatsApp-enabled phone number

    Returns:
        Dictionary with message SID and status

    Raises:
        Exception: If Twilio API call fails
    """
    try:
        # Send WhatsApp message via Twilio
        twilio_message = twilio_client.messages.create(
            from_=f'whatsapp:{twilio_phone}',
            to=f'whatsapp:{phone_number}',
            body=message_text
        )

        logger.info(f"WhatsApp sent successfully: {twilio_message.sid}")

        return {
            'sid': twilio_message.sid,
            'status': twilio_message.status,
            'success': True
        }

    except Exception as e:
        logger.error(f"Twilio API error: {str(e)}", exc_info=True)
        raise


def log_message_status(
    tracking_table,
    eum_msg_id: str,
    phone_number: str,
    message_text: str,
    twilio_message_id: str,
    status: str,
    timing_preference: str = '',
    student_name: str = '',
    error_message: str = ''
) -> None:
    """
    Log message delivery status to DynamoDB.

    Property 29: Sent messages logged to tracking table

    Args:
        tracking_table: DynamoDB table resource
        eum_msg_id: Unique message ID
        phone_number: Recipient phone
        message_text: Message content
        twilio_message_id: Twilio message SID
        status: Delivery status
        timing_preference: Student's timing preference
        student_name: Student's name
        error_message: Error details if failed
    """
    try:
        tracking_table.put_item(
            Item={
                'eum_msg_id': eum_msg_id,
                'phone_number': phone_number,
                'message_text': message_text,
                'twilio_message_id': twilio_message_id,
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'timing_preference': timing_preference,
                'student_name': student_name,
                'error_message': error_message
            }
        )

        logger.debug(f"Logged message status to DynamoDB: {eum_msg_id}")

    except Exception as e:
        logger.error(f"Failed to log to DynamoDB: {str(e)}", exc_info=True)
        # Don't raise - best effort logging


def process_sqs_message(
    message: Dict[str, Any],
    twilio_client,
    twilio_phone: str,
    tracking_table
) -> bool:
    """
    Process a single SQS message.

    Args:
        message: SQS message record
        twilio_client: Twilio client instance
        twilio_phone: Twilio phone number
        tracking_table: DynamoDB table resource

    Returns:
        True if successful, False otherwise
    """
    try:
        # Parse message body
        message_body = json.loads(message['body'])

        phone_number = message_body['phone_number']
        message_text = message_body['message']
        timing_preference = message_body.get('timing_preference', '')
        student_name = message_body.get('student_name', '')
        eum_msg_id = message_body['eum_msg_id']

        logger.info(f"Processing WhatsApp message to {phone_number}, ID: {eum_msg_id}")

        # Send WhatsApp message (Property 28)
        result = send_whatsapp_message(
            phone_number=phone_number,
            message_text=message_text,
            twilio_client=twilio_client,
            twilio_phone=twilio_phone
        )

        # Log delivery status to DynamoDB (Property 29)
        log_message_status(
            tracking_table=tracking_table,
            eum_msg_id=eum_msg_id,
            phone_number=phone_number,
            message_text=message_text,
            twilio_message_id=result['sid'],
            status=result['status'],
            timing_preference=timing_preference,
            student_name=student_name
        )

        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message body: {str(e)}")
        # Log error to tracking table
        try:
            message_body = json.loads(message.get('body', '{}'))
            log_message_status(
                tracking_table=tracking_table,
                eum_msg_id=message_body.get('eum_msg_id', 'unknown'),
                phone_number=message_body.get('phone_number', 'unknown'),
                message_text='',
                twilio_message_id='N/A',
                status='failed',
                error_message=f'Invalid JSON: {str(e)}'
            )
        except:
            pass
        return False

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)

        # Log error to tracking table (best effort)
        try:
            message_body = json.loads(message.get('body', '{}'))
            log_message_status(
                tracking_table=tracking_table,
                eum_msg_id=message_body.get('eum_msg_id', 'unknown'),
                phone_number=message_body.get('phone_number', 'unknown'),
                message_text=message_body.get('message', ''),
                twilio_message_id='N/A',
                status='failed',
                timing_preference=message_body.get('timing_preference', ''),
                student_name=message_body.get('student_name', ''),
                error_message=str(e)
            )
        except:
            pass

        # Re-raise to trigger SQS retry
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for WhatsApp sender.

    Input: SQS event with Records containing message data
    Output: None (logs to CloudWatch and DynamoDB)
    """
    logger.info(f"Processing {len(event['Records'])} SQS messages")

    # Initialize Twilio client
    try:
        from twilio.rest import Client

        twilio_client = Client(
            os.environ['TWILIO_ACCOUNT_SID'],
            os.environ['TWILIO_AUTH_TOKEN']
        )
        twilio_phone = os.environ['TWILIO_PHONE_NUMBER']

    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {str(e)}", exc_info=True)
        raise

    # Initialize DynamoDB table
    try:
        import boto3
        dynamodb = boto3.resource('dynamodb')
        tracking_table = dynamodb.Table(os.environ['MESSAGE_TRACKING_TABLE'])

    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB: {str(e)}", exc_info=True)
        raise

    # Process each message
    successful = 0
    failed = 0
    failures = []

    for record in event['Records']:
        try:
            success = process_sqs_message(
                message=record,
                twilio_client=twilio_client,
                twilio_phone=twilio_phone,
                tracking_table=tracking_table
            )

            if success:
                successful += 1
            else:
                failed += 1
                failures.append(record.get('messageId', 'unknown'))

        except Exception as e:
            failed += 1
            message_id = record.get('messageId', 'unknown')
            failures.append(message_id)
            logger.error(f"Failed to process message {message_id}: {str(e)}")

    logger.info(f"Processed {successful} successfully, {failed} failed")

    # If any messages failed, raise exception to trigger retry for failed messages
    if failed > 0:
        raise Exception(f"Failed to process {failed} messages: {failures}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': successful,
            'failed': failed
        })
    }
