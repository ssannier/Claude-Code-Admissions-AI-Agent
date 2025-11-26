"""
Unit tests for Form Submission Lambda

Tests validation logic and error handling with mocked Salesforce.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from form_submission import lambda_handler, validate_form_data, create_salesforce_lead


class TestFormValidation:
    """Test form validation logic (Property 1: Form validation rejects empty required fields)"""

    def test_valid_form_data(self):
        """Valid form data should pass validation"""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john.doe@example.com',
            'cellPhone': '+1-555-123-4567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        }

        is_valid, error = validate_form_data(form_data)
        assert is_valid is True
        assert error is None

    def test_missing_first_name(self):
        """Missing firstName should fail validation"""
        form_data = {
            'firstName': '',
            'lastName': 'Doe',
            'email': 'john@example.com',
            'cellPhone': '5551234567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        }

        is_valid, error = validate_form_data(form_data)
        assert is_valid is False
        assert 'firstName' in error

    def test_missing_email(self):
        """Missing email should fail validation"""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': '',
            'cellPhone': '5551234567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        }

        is_valid, error = validate_form_data(form_data)
        assert is_valid is False
        assert 'email' in error

    def test_invalid_email_format(self):
        """Invalid email format should fail validation"""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'notanemail',
            'cellPhone': '5551234567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        }

        is_valid, error = validate_form_data(form_data)
        assert is_valid is False
        assert 'email' in error.lower()

    def test_invalid_phone_number(self):
        """Phone number with less than 10 digits should fail validation"""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john@example.com',
            'cellPhone': '555',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        }

        is_valid, error = validate_form_data(form_data)
        assert is_valid is False
        assert 'phone' in error.lower()

    def test_optional_home_phone(self):
        """homePhone is optional and should not affect validation"""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john@example.com',
            'cellPhone': '5551234567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
            # No homePhone
        }

        is_valid, error = validate_form_data(form_data)
        assert is_valid is True
        assert error is None


class TestSalesforceIntegration:
    """Test Salesforce Lead creation (Property 2: Valid form submission creates Salesforce Lead)"""

    @patch('simple_salesforce.Salesforce')
    def test_successful_lead_creation(self, mock_salesforce):
        """Valid form data should create Salesforce Lead with correct fields"""
        # Mock Salesforce response
        mock_sf_instance = MagicMock()
        mock_sf_instance.Lead.create.return_value = {
            'id': '00Q5e000001abcDEFG',
            'success': True
        }
        mock_salesforce.return_value = mock_sf_instance

        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john@example.com',
            'cellPhone': '+15551234567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        }

        # Set required env vars
        os.environ['SF_USERNAME'] = 'test@example.com'
        os.environ['SF_PASSWORD'] = 'password'
        os.environ['SF_TOKEN'] = 'token'

        result = create_salesforce_lead(form_data)

        # Verify Lead was created
        assert result['success'] is True
        assert result['leadId'] == '00Q5e000001abcDEFG'

        # Verify correct data was sent to Salesforce
        call_args = mock_sf_instance.Lead.create.call_args[0][0]
        assert call_args['FirstName'] == 'John'
        assert call_args['LastName'] == 'Doe'
        assert call_args['Email'] == 'john@example.com'
        assert call_args['Phone'] == '+15551234567'
        assert call_args['LeadSource'] == 'Web Form - Admissions'
        assert call_args['Status'] == 'New'
        assert call_args['Company'] == 'Not Provided'

    @patch('simple_salesforce.Salesforce')
    def test_lead_creation_with_optional_fields(self, mock_salesforce):
        """Lead creation should include optional homePhone in description"""
        mock_sf_instance = MagicMock()
        mock_sf_instance.Lead.create.return_value = {
            'id': '00Q5e000001abcDEFG',
            'success': True
        }
        mock_salesforce.return_value = mock_sf_instance

        form_data = {
            'firstName': 'Jane',
            'lastName': 'Smith',
            'email': 'jane@example.com',
            'cellPhone': '+15551234567',
            'homePhone': '+15559876543',
            'headquarters': 'Makati',
            'programType': 'Graduate'
        }

        os.environ['SF_USERNAME'] = 'test@example.com'
        os.environ['SF_PASSWORD'] = 'password'
        os.environ['SF_TOKEN'] = 'token'

        create_salesforce_lead(form_data)

        # Verify homePhone was included in description
        call_args = mock_sf_instance.Lead.create.call_args[0][0]
        assert 'Home Phone: +15559876543' in call_args['Description']


class TestLambdaHandler:
    """Test complete Lambda handler flow"""

    @patch('simple_salesforce.Salesforce')
    def test_successful_form_submission(self, mock_salesforce):
        """Valid form submission should return 200 with success message"""
        mock_sf_instance = MagicMock()
        mock_sf_instance.Lead.create.return_value = {
            'id': '00Q5e000001abcDEFG',
            'success': True
        }
        mock_salesforce.return_value = mock_sf_instance

        event = {
            'body': json.dumps({
                'firstName': 'John',
                'lastName': 'Doe',
                'email': 'john@example.com',
                'cellPhone': '+15551234567',
                'headquarters': 'Manila',
                'programType': 'Undergraduate'
            })
        }

        os.environ['SF_USERNAME'] = 'test@example.com'
        os.environ['SF_PASSWORD'] = 'password'
        os.environ['SF_TOKEN'] = 'token'

        # Mock context
        context = Mock()
        context.request_id = 'test-request-id'

        response = lambda_handler(event, context)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'leadId' in body
        assert body['leadId'] == '00Q5e000001abcDEFG'

    def test_invalid_form_data_returns_400(self):
        """Invalid form data should return 400 with error message"""
        event = {
            'body': json.dumps({
                'firstName': '',  # Missing required field
                'lastName': 'Doe',
                'email': 'john@example.com',
                'cellPhone': '5551234567',
                'headquarters': 'Manila',
                'programType': 'Undergraduate'
            })
        }

        context = Mock()
        context.request_id = 'test-request-id'

        response = lambda_handler(event, context)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'firstName' in body['message']

    @patch('simple_salesforce.Salesforce')
    def test_salesforce_error_returns_500(self, mock_salesforce):
        """Salesforce connection error should return 500 with user-friendly message"""
        mock_salesforce.side_effect = Exception("Salesforce connection failed")

        event = {
            'body': json.dumps({
                'firstName': 'John',
                'lastName': 'Doe',
                'email': 'john@example.com',
                'cellPhone': '+15551234567',
                'headquarters': 'Manila',
                'programType': 'Undergraduate'
            })
        }

        os.environ['SF_USERNAME'] = 'test@example.com'
        os.environ['SF_PASSWORD'] = 'password'
        os.environ['SF_TOKEN'] = 'token'

        context = Mock()
        context.request_id = 'test-request-id'

        response = lambda_handler(event, context)

        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        # Verify no technical details exposed
        assert 'Salesforce' not in body['message']
        assert 'connection' not in body['message'].lower()

    def test_invalid_json_returns_400(self):
        """Invalid JSON should return 400 error"""
        event = {
            'body': 'not valid json'
        }

        context = Mock()
        context.request_id = 'test-request-id'

        response = lambda_handler(event, context)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False

    def test_cors_headers_present(self):
        """Response should include CORS headers"""
        event = {
            'body': json.dumps({
                'firstName': '',
                'lastName': 'Doe',
                'email': 'john@example.com',
                'cellPhone': '5551234567',
                'headquarters': 'Manila',
                'programType': 'Undergraduate'
            })
        }

        context = Mock()
        context.request_id = 'test-request-id'

        response = lambda_handler(event, context)

        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
