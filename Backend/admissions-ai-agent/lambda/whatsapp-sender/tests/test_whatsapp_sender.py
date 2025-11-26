"""
Unit tests for WhatsApp Sender Lambda

Tests Twilio integration and DynamoDB logging with mocks.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from send_whatsapp_twilio import (
    lambda_handler,
    send_whatsapp_message,
    log_message_status,
    process_sqs_message
)


class TestSendWhatsAppMessage:
    """Test Twilio WhatsApp message sending (Property 28)"""

    def test_successful_message_send(self):
        """Successfully send WhatsApp message via Twilio"""
        # Mock Twilio client
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = 'SM1234567890abcdef'
        mock_message.status = 'sent'
        mock_client.messages.create.return_value = mock_message

        result = send_whatsapp_message(
            phone_number='+15551234567',
            message_text='Test message',
            twilio_client=mock_client,
            twilio_phone='+15559876543'
        )

        # Verify result
        assert result['success'] is True
        assert result['sid'] == 'SM1234567890abcdef'
        assert result['status'] == 'sent'

        # Verify Twilio was called correctly
        mock_client.messages.create.assert_called_once_with(
            from_='whatsapp:+15559876543',
            to='whatsapp:+15551234567',
            body='Test message'
        )

    def test_twilio_api_error(self):
        """Twilio API error should raise exception"""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Twilio API error")

        with pytest.raises(Exception, match="Twilio API error"):
            send_whatsapp_message(
                phone_number='+15551234567',
                message_text='Test message',
                twilio_client=mock_client,
                twilio_phone='+15559876543'
            )


class TestLogMessageStatus:
    """Test DynamoDB message tracking (Property 29)"""

    def test_successful_status_logging(self):
        """Successfully log message status to DynamoDB"""
        mock_table = MagicMock()

        log_message_status(
            tracking_table=mock_table,
            eum_msg_id='test-uuid-123',
            phone_number='+15551234567',
            message_text='Test message',
            twilio_message_id='SM1234567890abcdef',
            status='sent',
            timing_preference='2 hours',
            student_name='John Doe'
        )

        # Verify DynamoDB was called
        mock_table.put_item.assert_called_once()

        # Verify correct data structure
        call_args = mock_table.put_item.call_args[1]['Item']
        assert call_args['eum_msg_id'] == 'test-uuid-123'
        assert call_args['phone_number'] == '+15551234567'
        assert call_args['message_text'] == 'Test message'
        assert call_args['twilio_message_id'] == 'SM1234567890abcdef'
        assert call_args['status'] == 'sent'
        assert call_args['timing_preference'] == '2 hours'
        assert call_args['student_name'] == 'John Doe'
        assert 'timestamp' in call_args

    def test_logging_with_error_message(self):
        """Log failed message with error details"""
        mock_table = MagicMock()

        log_message_status(
            tracking_table=mock_table,
            eum_msg_id='test-uuid-123',
            phone_number='+15551234567',
            message_text='Test message',
            twilio_message_id='N/A',
            status='failed',
            error_message='Connection timeout'
        )

        call_args = mock_table.put_item.call_args[1]['Item']
        assert call_args['status'] == 'failed'
        assert call_args['error_message'] == 'Connection timeout'

    def test_dynamodb_error_doesnt_raise(self):
        """DynamoDB logging error should not raise exception (best effort)"""
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")

        # Should not raise
        log_message_status(
            tracking_table=mock_table,
            eum_msg_id='test-uuid-123',
            phone_number='+15551234567',
            message_text='Test message',
            twilio_message_id='SM123',
            status='sent'
        )


class TestProcessSQSMessage:
    """Test SQS message processing"""

    def test_successful_message_processing(self):
        """Successfully process SQS message"""
        # Mock Twilio client
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = 'SM123'
        mock_message.status = 'sent'
        mock_client.messages.create.return_value = mock_message

        # Mock DynamoDB table
        mock_table = MagicMock()

        # Create SQS message
        sqs_message = {
            'body': json.dumps({
                'phone_number': '+15551234567',
                'message': 'Your advisor will contact you soon!',
                'timing_preference': '2 hours',
                'student_name': 'John Doe',
                'eum_msg_id': 'test-uuid-123'
            })
        }

        result = process_sqs_message(
            message=sqs_message,
            twilio_client=mock_client,
            twilio_phone='+15559876543',
            tracking_table=mock_table
        )

        assert result is True
        mock_client.messages.create.assert_called_once()
        mock_table.put_item.assert_called_once()

    def test_invalid_json_in_message(self):
        """Invalid JSON in SQS message should return False"""
        mock_client = MagicMock()
        mock_table = MagicMock()

        sqs_message = {
            'body': 'not valid json'
        }

        result = process_sqs_message(
            message=sqs_message,
            twilio_client=mock_client,
            twilio_phone='+15559876543',
            tracking_table=mock_table
        )

        assert result is False

    def test_twilio_error_raises_for_retry(self):
        """Twilio error should raise to trigger SQS retry"""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Twilio error")
        mock_table = MagicMock()

        sqs_message = {
            'body': json.dumps({
                'phone_number': '+15551234567',
                'message': 'Test',
                'eum_msg_id': 'test-uuid'
            })
        }

        with pytest.raises(Exception, match="Twilio error"):
            process_sqs_message(
                message=sqs_message,
                twilio_client=mock_client,
                twilio_phone='+15559876543',
                tracking_table=mock_table
            )

        # Verify error was logged to DynamoDB
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        assert call_args['status'] == 'failed'


class TestLambdaHandler:
    """Test complete Lambda handler flow"""

    @patch('boto3.resource')
    @patch('twilio.rest.Client')
    def test_successful_batch_processing(self, mock_twilio_client_class, mock_boto3):
        """Successfully process batch of SQS messages"""
        # Mock Twilio
        mock_client_instance = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = 'SM123'
        mock_message.status = 'sent'
        mock_client_instance.messages.create.return_value = mock_message
        mock_twilio_client_class.return_value = mock_client_instance

        # Mock DynamoDB
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.return_value = mock_dynamodb

        # Set environment variables
        os.environ['TWILIO_ACCOUNT_SID'] = 'ACtest'
        os.environ['TWILIO_AUTH_TOKEN'] = 'test_token'
        os.environ['TWILIO_PHONE_NUMBER'] = '+15559876543'
        os.environ['MESSAGE_TRACKING_TABLE'] = 'WhatsAppMessageTracking'

        # Create event with multiple messages
        event = {
            'Records': [
                {
                    'body': json.dumps({
                        'phone_number': '+15551111111',
                        'message': 'Message 1',
                        'eum_msg_id': 'uuid-1'
                    }),
                    'messageId': 'msg-1'
                },
                {
                    'body': json.dumps({
                        'phone_number': '+15552222222',
                        'message': 'Message 2',
                        'eum_msg_id': 'uuid-2'
                    }),
                    'messageId': 'msg-2'
                }
            ]
        }

        context = Mock()

        response = lambda_handler(event, context)

        # Verify success
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['processed'] == 2
        assert body['failed'] == 0

        # Verify Twilio was called twice
        assert mock_client_instance.messages.create.call_count == 2

        # Verify DynamoDB was called twice
        assert mock_table.put_item.call_count == 2

    @patch('boto3.resource')
    @patch('twilio.rest.Client')
    def test_partial_batch_failure(self, mock_twilio_client_class, mock_boto3):
        """Handle partial batch failure and raise exception for retry"""
        # Mock Twilio - first succeeds, second fails
        mock_client_instance = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = 'SM123'
        mock_message.status = 'sent'
        mock_client_instance.messages.create.side_effect = [
            mock_message,
            Exception("Twilio error")
        ]
        mock_twilio_client_class.return_value = mock_client_instance

        # Mock DynamoDB
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.return_value = mock_dynamodb

        os.environ['TWILIO_ACCOUNT_SID'] = 'ACtest'
        os.environ['TWILIO_AUTH_TOKEN'] = 'test_token'
        os.environ['TWILIO_PHONE_NUMBER'] = '+15559876543'
        os.environ['MESSAGE_TRACKING_TABLE'] = 'WhatsAppMessageTracking'

        event = {
            'Records': [
                {
                    'body': json.dumps({
                        'phone_number': '+15551111111',
                        'message': 'Message 1',
                        'eum_msg_id': 'uuid-1'
                    }),
                    'messageId': 'msg-1'
                },
                {
                    'body': json.dumps({
                        'phone_number': '+15552222222',
                        'message': 'Message 2',
                        'eum_msg_id': 'uuid-2'
                    }),
                    'messageId': 'msg-2'
                }
            ]
        }

        context = Mock()

        # Should raise exception due to failure
        with pytest.raises(Exception, match="Failed to process 1 messages"):
            lambda_handler(event, context)

    @patch('boto3.resource')
    @patch('twilio.rest.Client')
    def test_twilio_initialization_failure(self, mock_twilio_client_class, mock_boto3):
        """Twilio client initialization failure should raise"""
        mock_twilio_client_class.side_effect = Exception("Invalid credentials")

        os.environ['TWILIO_ACCOUNT_SID'] = 'invalid'
        os.environ['TWILIO_AUTH_TOKEN'] = 'invalid'
        os.environ['TWILIO_PHONE_NUMBER'] = '+15559876543'
        os.environ['MESSAGE_TRACKING_TABLE'] = 'WhatsAppMessageTracking'

        event = {'Records': []}
        context = Mock()

        with pytest.raises(Exception, match="Failed to initialize Twilio client"):
            lambda_handler(event, context)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
