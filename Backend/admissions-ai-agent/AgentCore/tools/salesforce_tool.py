"""
Salesforce CRM Tool

Provides functions for querying Leads and creating Tasks in Salesforce.
Property 11: Agent queries Salesforce for Lead status
Property 12: Agent creates Salesforce Tasks for human follow-up
"""

import os
import logging
from typing import Dict, Any, List, Optional
from strands import tool
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed

logger = logging.getLogger(__name__)


def get_salesforce_client() -> Salesforce:
    """
    Initialize and return Salesforce client.

    Returns:
        Authenticated Salesforce client

    Raises:
        Exception: If authentication fails
    """
    try:
        return Salesforce(
            username=os.environ['SF_USERNAME'],
            password=os.environ['SF_PASSWORD'],
            security_token=os.environ['SF_TOKEN']
        )
    except SalesforceAuthenticationFailed as e:
        logger.error(f"Salesforce authentication failed: {str(e)}")
        raise Exception("Unable to connect to student database")
    except KeyError as e:
        logger.error(f"Missing Salesforce credentials: {str(e)}")
        raise Exception("Salesforce configuration error")


@tool
def query_salesforce_leads(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    last_name: Optional[str] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """Query Salesforce for student leads by email, phone, or name.

    This tool searches the student database (Salesforce CRM) to find leads
    that match the provided criteria. Use this when a student asks about
    their application status or when you need to retrieve student information.

    Property 11: Agent queries Salesforce for Lead status

    Args:
        email: Student's email address
        phone: Student's phone number
        last_name: Student's last name
        limit: Maximum number of results to return (default: 5)

    Returns:
        Search results with lead information including status, contact details,
        program interests, and submission dates
    """
    try:
        sf = get_salesforce_client()

        # Build SOQL query
        conditions = []
        if email:
            conditions.append(f"Email = '{email}'")
        if phone:
            # Normalize phone for search
            normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '')
            conditions.append(f"Phone LIKE '%{normalized_phone}%'")
        if last_name:
            conditions.append(f"LastName = '{last_name}'")

        if not conditions:
            return {
                "status": "error",
                "content": [{"text": "Please provide at least one search criterion (email, phone, or last name)"}]
            }

        where_clause = " OR ".join(conditions)

        query = f"""
            SELECT Id, FirstName, LastName, Email, Phone, Status, LeadSource,
                   Program_Type__c, Headquarters__c, Timing_Preference__c,
                   CreatedDate, LastModifiedDate
            FROM Lead
            WHERE {where_clause}
            ORDER BY LastModifiedDate DESC
            LIMIT {limit}
        """

        logger.info(f"Querying Salesforce with: {query}")
        results = sf.query(query)

        if results['totalSize'] == 0:
            return {
                "status": "success",
                "content": [{
                    "text": "No student records found matching the search criteria. The student may not have submitted an application yet."
                }]
            }

        # Format results
        leads = []
        for record in results['records']:
            lead_info = {
                "id": record['Id'],
                "name": f"{record.get('FirstName', '')} {record.get('LastName', '')}".strip(),
                "email": record.get('Email'),
                "phone": record.get('Phone'),
                "status": record.get('Status'),
                "lead_source": record.get('LeadSource'),
                "program_type": record.get('Program_Type__c'),
                "headquarters": record.get('Headquarters__c'),
                "timing_preference": record.get('Timing_Preference__c'),
                "created_date": record.get('CreatedDate'),
                "last_modified": record.get('LastModifiedDate')
            }
            leads.append(lead_info)

        response_text = f"Found {results['totalSize']} student record(s):\n\n"
        for lead in leads:
            response_text += f"**{lead['name']}**\n"
            response_text += f"- Status: {lead['status']}\n"
            response_text += f"- Program: {lead['program_type']} at {lead['headquarters']}\n"
            response_text += f"- Contact: {lead['email']}, {lead['phone']}\n"
            response_text += f"- Timing Preference: {lead['timing_preference']}\n"
            response_text += f"- Application Date: {lead['created_date']}\n\n"

        return {
            "status": "success",
            "content": [{"text": response_text}],
            "data": leads
        }

    except Exception as e:
        logger.error(f"Error querying Salesforce: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "content": [{"text": f"I'm having trouble accessing the student database right now. Please try again in a moment."}]
        }


@tool
def create_salesforce_task(
    lead_email: str,
    subject: str,
    description: str,
    priority: str = "Normal",
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a follow-up task in Salesforce for a human advisor.

    Use this tool when a student's question requires human intervention,
    when you need to escalate a complex issue, or when scheduling a
    follow-up action. This creates a task assigned to the advisor team.

    Property 12: Agent creates Salesforce Tasks for human follow-up

    Args:
        lead_email: Email of the student (to link the task to their Lead record)
        subject: Brief subject line for the task (e.g., "Follow up on program requirements")
        description: Detailed description of what needs to be done
        priority: Task priority - "High", "Normal", or "Low" (default: "Normal")
        due_date: Due date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        Confirmation that the task was created successfully
    """
    try:
        sf = get_salesforce_client()

        # Find the Lead record
        query = f"SELECT Id FROM Lead WHERE Email = '{lead_email}' LIMIT 1"
        lead_results = sf.query(query)

        if lead_results['totalSize'] == 0:
            return {
                "status": "error",
                "content": [{"text": f"Could not find student record with email: {lead_email}"}]
            }

        lead_id = lead_results['records'][0]['Id']

        # Create task
        task_data = {
            'WhoId': lead_id,
            'Subject': subject,
            'Description': description,
            'Priority': priority,
            'Status': 'Not Started',
            'ActivityDate': due_date if due_date else None
        }

        result = sf.Task.create(task_data)

        if result['success']:
            logger.info(f"Created Salesforce task {result['id']} for lead {lead_id}")
            return {
                "status": "success",
                "content": [{
                    "text": f"✓ I've created a task for our admissions team to follow up on: '{subject}'. A human advisor will reach out soon to help with this."
                }],
                "task_id": result['id']
            }
        else:
            return {
                "status": "error",
                "content": [{"text": "Failed to create follow-up task. Please contact admissions@university.edu directly."}]
            }

    except Exception as e:
        logger.error(f"Error creating Salesforce task: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "content": [{"text": "I'm having trouble creating a follow-up task. Please email admissions@university.edu for assistance."}]
        }


# Helper functions for advisor handoff workflow

def search_lead_by_phone(phone_number: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Search for a Lead by phone number.

    Property 20: Phone number used to search Salesforce for Lead

    Args:
        phone_number: Phone number to search for

    Returns:
        Tuple of (lead_id, lead_data) or (None, None) if not found
    """
    try:
        from tools.session_utils import sanitize_phone_for_actor_id

        sf = get_salesforce_client()

        # Sanitize phone
        sanitized_phone = sanitize_phone_for_actor_id(phone_number)
        normalized = sanitized_phone.replace('+', '').replace('-', '').replace(' ', '')

        # Search for Lead
        query = f"""
            SELECT Id, FirstName, LastName, Email, Phone, Status,
                   Program_Type__c, Headquarters__c
            FROM Lead
            WHERE Phone LIKE '%{normalized}%'
            ORDER BY LastModifiedDate DESC
            LIMIT 1
        """

        results = sf.query(query)

        if results['totalSize'] > 0:
            record = results['records'][0]
            lead_data = {
                'id': record['Id'],
                'first_name': record.get('FirstName', ''),
                'last_name': record.get('LastName', ''),
                'email': record.get('Email', ''),
                'phone': record.get('Phone', ''),
                'status': record.get('Status', ''),
                'program_type': record.get('Program_Type__c', ''),
                'headquarters': record.get('Headquarters__c', '')
            }
            return record['Id'], lead_data

        return None, None

    except Exception as e:
        logger.error(f"Error searching Lead by phone: {str(e)}", exc_info=True)
        return None, None


def update_lead_status(lead_id: str, status: str = "Working") -> bool:
    """
    Update Lead status in Salesforce.

    Property 21: Lead status updated to "Working"

    Args:
        lead_id: Salesforce Lead ID
        status: New status (default: "Working")

    Returns:
        True if successful, False otherwise
    """
    try:
        sf = get_salesforce_client()

        result = sf.Lead.update(lead_id, {'Status': status})

        if result == 204:  # Success response code
            logger.info(f"Updated Lead {lead_id} status to {status}")
            return True

        return False

    except Exception as e:
        logger.error(f"Error updating Lead status: {str(e)}", exc_info=True)
        return False


def create_task_with_full_history(
    lead_id: str,
    student_name: str,
    task_description: str,
    conversation_history: str = ""
) -> Optional[str]:
    """
    Create a Salesforce Task with full conversation history.

    Properties 23-25: Task includes conversation transcript

    Args:
        lead_id: Salesforce Lead ID
        student_name: Student's name
        task_description: Brief description of the task
        conversation_history: Full conversation transcript

    Returns:
        Task ID if successful, None otherwise
    """
    try:
        sf = get_salesforce_client()

        # Combine description with conversation history
        full_description = f"{task_description}\n\n"

        if conversation_history:
            full_description += "--- Conversation Transcript ---\n"
            full_description += conversation_history

        # Truncate if too long (Salesforce Description field limit is 32KB)
        if len(full_description) > 30000:
            full_description = full_description[:30000] + "\n\n[Transcript truncated]"

        task_data = {
            'WhoId': lead_id,
            'Subject': f"Advisor Handoff: {student_name}",
            'Description': full_description,
            'Priority': 'High',
            'Status': 'Not Started',
            'Type': 'Advisor Handoff'
        }

        result = sf.Task.create(task_data)

        if result['success']:
            logger.info(f"Created Task {result['id']} with full history for Lead {lead_id}")
            return result['id']

        return None

    except Exception as e:
        logger.error(f"Error creating Task with history: {str(e)}", exc_info=True)
        return None
