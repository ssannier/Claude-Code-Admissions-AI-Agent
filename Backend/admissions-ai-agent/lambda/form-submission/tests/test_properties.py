"""
Property-based tests for Form Submission Lambda

Uses Hypothesis to test correctness properties with randomly generated data.
"""

import json
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from form_submission import validate_form_data, lambda_handler


# Custom strategies for form data
@st.composite
def form_data_with_empty_fields(draw):
    """Generate form data with at least one empty required field"""
    fields = {
        'firstName': draw(st.one_of(st.just(''), st.just(None), st.text(min_size=1, max_size=50))),
        'lastName': draw(st.one_of(st.just(''), st.just(None), st.text(min_size=1, max_size=50))),
        'email': draw(st.one_of(st.just(''), st.just(None), st.emails())),
        'cellPhone': draw(st.one_of(st.just(''), st.just(None), st.text(min_size=10, max_size=15))),
        'headquarters': draw(st.one_of(st.just(''), st.just(None), st.sampled_from(['Manila', 'Makati', 'Cebu']))),
        'programType': draw(st.one_of(st.just(''), st.just(None), st.sampled_from(['Undergraduate', 'Graduate', 'Doctorate'])))
    }

    # Ensure at least one field is empty
    if all(fields.values()):
        empty_field = draw(st.sampled_from(list(fields.keys())))
        fields[empty_field] = ''

    return fields


@st.composite
def valid_form_data(draw):
    """Generate valid form data"""
    return {
        'firstName': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        'lastName': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        'email': draw(st.emails()),
        'cellPhone': '+1' + draw(st.text(min_size=10, max_size=10, alphabet='0123456789')),
        'headquarters': draw(st.sampled_from(['Manila', 'Makati', 'Cebu', 'Davao'])),
        'programType': draw(st.sampled_from(['Undergraduate', 'Graduate', 'Doctorate']))
    }


class TestFormValidationProperties:
    """Property-based tests for form validation"""

    @settings(max_examples=100)
    @given(form_data_with_empty_fields())
    def test_property_1_form_validation_rejects_empty_fields(self, form_data):
        """
        Feature: ai-admissions-agent, Property 1: Form validation rejects empty required fields

        Any form submission with empty required fields should be rejected.
        """
        is_valid, error = validate_form_data(form_data)

        # If any required field is empty/None, validation should fail
        required_fields = ['firstName', 'lastName', 'email', 'cellPhone', 'headquarters', 'programType']
        has_empty_field = any(
            not form_data.get(field) or not str(form_data.get(field)).strip()
            for field in required_fields
        )

        if has_empty_field:
            assert is_valid is False, f"Validation should reject empty fields: {form_data}"
            assert error is not None, "Error message should be provided"
        # If all required fields are present, could still fail on email/phone format validation

    @settings(max_examples=100)
    @given(st.text(max_size=20))
    def test_email_without_at_symbol_rejected(self, text):
        """Email without @ symbol should be rejected"""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': text,  # Random text without @ symbol
            'cellPhone': '5551234567',
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        }

        is_valid, error = validate_form_data(form_data)

        if '@' not in text or '.' not in text:
            assert is_valid is False
            assert error is not None

    @settings(max_examples=100)
    @given(st.text(min_size=1, max_size=9, alphabet='0123456789'))
    def test_phone_with_less_than_10_digits_rejected(self, phone):
        """Phone numbers with less than 10 digits should be rejected"""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john@example.com',
            'cellPhone': phone,
            'headquarters': 'Manila',
            'programType': 'Undergraduate'
        }

        is_valid, error = validate_form_data(form_data)

        # Since phone has less than 10 digits, should be rejected
        assert is_valid is False
        assert error is not None
        assert 'phone' in error.lower()


class TestLambdaHandlerProperties:
    """Property-based tests for Lambda handler"""

    @settings(max_examples=50)
    @given(form_data_with_empty_fields())
    def test_invalid_form_returns_400(self, form_data):
        """Any invalid form data should return 400 status code"""
        event = {
            'body': json.dumps(form_data)
        }

        context = Mock()
        context.request_id = 'test-request-id'

        response = lambda_handler(event, context)

        # If validation fails, should return 400
        is_valid, _ = validate_form_data(form_data)
        if not is_valid:
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['success'] is False

    @settings(max_examples=50)
    @given(valid_form_data())
    @patch('simple_salesforce.Salesforce')
    def test_property_2_valid_form_creates_lead(self, mock_salesforce, form_data):
        """
        Feature: ai-admissions-agent, Property 2: Valid form submission creates Salesforce Lead

        Valid form data should create a Lead with LeadSource "Web Form - Admissions" and Status "New".
        """
        # Mock Salesforce success response
        mock_sf_instance = MagicMock()
        mock_sf_instance.Lead.create.return_value = {
            'id': '00Q5e000001abcDEFG',
            'success': True
        }
        mock_salesforce.return_value = mock_sf_instance

        event = {
            'body': json.dumps(form_data)
        }

        os.environ['SF_USERNAME'] = 'test@example.com'
        os.environ['SF_PASSWORD'] = 'password'
        os.environ['SF_TOKEN'] = 'token'

        context = Mock()
        context.request_id = 'test-request-id'

        response = lambda_handler(event, context)

        # Verify validation passes
        is_valid, _ = validate_form_data(form_data)

        if is_valid:
            # Should return success
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True

            # Verify Salesforce was called with correct data
            if mock_sf_instance.Lead.create.called:
                call_args = mock_sf_instance.Lead.create.call_args[0][0]
                assert call_args['LeadSource'] == 'Web Form - Admissions'
                assert call_args['Status'] == 'New'
                assert call_args['FirstName'] == form_data['firstName']
                assert call_args['LastName'] == form_data['lastName']
                assert call_args['Email'] == form_data['email']

    @settings(max_examples=50)
    @given(valid_form_data())
    @patch('simple_salesforce.Salesforce')
    def test_salesforce_error_hides_technical_details(self, mock_salesforce, form_data):
        """
        Salesforce errors should return user-friendly messages without technical details.

        This verifies error handling property: never expose technical details to users.
        """
        # Mock Salesforce failure
        mock_salesforce.side_effect = Exception("INVALID_SESSION_ID: Session expired or invalid")

        event = {
            'body': json.dumps(form_data)
        }

        os.environ['SF_USERNAME'] = 'test@example.com'
        os.environ['SF_PASSWORD'] = 'password'
        os.environ['SF_TOKEN'] = 'token'

        context = Mock()
        context.request_id = 'test-request-id'

        response = lambda_handler(event, context)

        is_valid, _ = validate_form_data(form_data)

        if is_valid:
            # Should return 500 error
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['success'] is False

            # Verify no technical details exposed
            message_lower = body['message'].lower()
            assert 'session' not in message_lower
            assert 'expired' not in message_lower
            assert 'invalid_session_id' not in message_lower
            assert 'salesforce' not in message_lower

    @settings(max_examples=50)
    @given(st.text(min_size=1, max_size=100))
    def test_invalid_json_returns_400(self, text):
        """Invalid JSON in request body should return 400"""
        # Only test strings that are NOT valid JSON
        try:
            json.loads(text)
            is_valid_json = True
        except:
            is_valid_json = False

        if not is_valid_json:
            event = {
                'body': text
            }

            context = Mock()
            context.request_id = 'test-request-id'

            response = lambda_handler(event, context)

            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
