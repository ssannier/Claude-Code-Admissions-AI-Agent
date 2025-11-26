"""
Form Submission Lambda Handler

Creates Salesforce Leads from inquiry form submissions.
Validates form data and returns user-friendly error messages.
"""

import json
import os
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))


def validate_form_data(body: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate required form fields.

    Property 1: Form validation rejects empty required fields

    Args:
        body: Form data dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['firstName', 'lastName', 'email', 'cellPhone', 'headquarters', 'programType']

    for field in required_fields:
        if not body.get(field) or not str(body.get(field)).strip():
            return False, f"Missing required field: {field}"

    # Basic email validation
    email = body.get('email', '')
    if '@' not in email or '.' not in email:
        return False, "Invalid email address"

    # Basic phone validation (at least 10 digits)
    cell_phone = ''.join(filter(str.isdigit, body.get('cellPhone', '')))
    if len(cell_phone) < 10:
        return False, "Invalid phone number - must be at least 10 digits"

    return True, None


def create_salesforce_lead(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create Salesforce Lead from form data.

    Property 2: Valid form submission creates Salesforce Lead

    Args:
        form_data: Validated form data

    Returns:
        Dictionary with Lead ID

    Raises:
        Exception: If Salesforce connection or Lead creation fails
    """
    try:
        from simple_salesforce import Salesforce

        # Connect to Salesforce
        sf = Salesforce(
            username=os.environ['SF_USERNAME'],
            password=os.environ['SF_PASSWORD'],
            security_token=os.environ['SF_TOKEN']
        )

        # Prepare Lead data
        lead_data = {
            'FirstName': form_data['firstName'],
            'LastName': form_data['lastName'],
            'Email': form_data['email'],
            'Phone': form_data['cellPhone'],
            'Description': f"Headquarters: {form_data['headquarters']}\nProgram Type: {form_data['programType']}",
            'Company': 'Not Provided',  # Required field
            'LeadSource': 'Web Form - Admissions',
            'Status': 'New'
        }

        # Add home phone if provided
        if form_data.get('homePhone'):
            lead_data['Description'] += f"\nHome Phone: {form_data['homePhone']}"

        # Create Lead
        result = sf.Lead.create(lead_data)

        logger.info(f"Successfully created Lead: {result['id']}")

        return {
            'leadId': result['id'],
            'success': result['success']
        }

    except Exception as e:
        logger.error(f"Salesforce error: {str(e)}", exc_info=True)
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for form submission.

    Input: API Gateway event with form data in body
    Output: {statusCode: 200, body: {success: true, message: "..."}}
    """
    logger.info(f"Processing form submission, request ID: {context.request_id if context else 'local'}")

    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))

        logger.debug(f"Form data: {json.dumps({k: v for k, v in body.items() if k != 'homePhone'})}")

        # Validate form data (Property 1)
        is_valid, error_message = validate_form_data(body)
        if not is_valid:
            logger.warning(f"Form validation failed: {error_message}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',  # TODO: Restrict in production
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'message': error_message
                })
            }

        # Create Salesforce Lead (Property 2)
        try:
            lead_result = create_salesforce_lead(body)

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'Your inquiry has been submitted successfully. Please check your email for confirmation.',
                    'leadId': lead_result['leadId']
                })
            }

        except Exception as sf_error:
            logger.error(f"Failed to create Salesforce Lead: {str(sf_error)}", exc_info=True)

            # Return user-friendly error (never expose technical details)
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'message': 'We encountered an error processing your request. Please try again in a moment.'
                })
            }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'message': 'Invalid request format'
            })
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            })
        }
