"""
Knowledge Base Search Tool

Searches admissions documentation in S3-based knowledge base.
Property 10: Agent searches S3 knowledge base for admissions information
"""

import os
import logging
from typing import Dict, Any, List
from strands import tool
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_s3_client():
    """Get S3 client instance."""
    return boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))


def search_knowledge_base_s3(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Search knowledge base files in S3 for relevant content.

    This is a simplified implementation that reads markdown files from S3.
    In production, this would use Amazon Bedrock Knowledge Base with vector search.

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        List of relevant documents with content
    """
    try:
        s3 = get_s3_client()
        bucket_name = os.environ['KNOWLEDGE_BASE_BUCKET']

        # List all markdown files
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix='admissions/'
        )

        if 'Contents' not in response:
            return []

        results = []

        # Simple keyword search (in production, use Bedrock KB with embeddings)
        query_lower = query.lower()

        for obj in response.get('Contents', [])[:10]:  # Limit to first 10 files
            if not obj['Key'].endswith(('.md', '.txt')):
                continue

            try:
                # Get file content
                file_obj = s3.get_object(Bucket=bucket_name, Key=obj['Key'])
                content = file_obj['Body'].read().decode('utf-8')

                # Check if query keywords are in content
                if any(keyword in content.lower() for keyword in query_lower.split()):
                    results.append({
                        'file': obj['Key'],
                        'content': content[:2000],  # First 2000 chars
                        'size': obj['Size']
                    })

                    if len(results) >= max_results:
                        break

            except Exception as e:
                logger.warning(f"Error reading {obj['Key']}: {str(e)}")
                continue

        return results

    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
        return []


@tool
def search_admissions_knowledge(
    query: str,
    topic: str = "general"
) -> Dict[str, Any]:
    """Search the university's admissions knowledge base for information.

    Use this tool to find accurate, official information about:
    - Admission requirements and deadlines
    - Program offerings and details
    - Application procedures
    - Tuition and financial aid
    - Campus information
    - Academic policies

    Always use this tool before answering specific questions about university
    policies, requirements, or procedures to ensure accuracy.

    Property 10: Agent searches S3 knowledge base for admissions information

    Args:
        query: Search query describing what information is needed
               (e.g., "undergraduate admission requirements", "graduate program deadlines")
        topic: Topic category - "requirements", "programs", "deadlines", "financial",
               "campus", or "general" (default: "general")

    Returns:
        Relevant information from the knowledge base with sources
    """
    try:
        # Search knowledge base
        results = search_knowledge_base_s3(query, max_results=3)

        if not results:
            return {
                "status": "success",
                "content": [{
                    "text": "I couldn't find specific information about that in our knowledge base. Let me create a task for a human advisor to provide you with accurate details, or you can visit our website at admissions.university.edu."
                }]
            }

        # Format results
        response_text = f"Based on our admissions documentation:\n\n"

        for i, result in enumerate(results, 1):
            file_name = result['file'].split('/')[-1]
            content_preview = result['content'][:500]  # First 500 chars

            response_text += f"**Source {i}: {file_name}**\n"
            response_text += f"{content_preview}\n\n"

            if len(content_preview) == 500:
                response_text += "...\n\n"

        response_text += f"*Found {len(results)} relevant document(s). For complete details, please visit our admissions website or contact an advisor.*"

        return {
            "status": "success",
            "content": [{"text": response_text}],
            "sources": [r['file'] for r in results],
            "result_count": len(results)
        }

    except KeyError as e:
        logger.error(f"Missing configuration: {str(e)}")
        return {
            "status": "error",
            "content": [{
                "text": "The knowledge base is not currently available. Please visit admissions.university.edu or let me connect you with a human advisor."
            }]
        }

    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "content": [{
                "text": "I'm having trouble accessing the knowledge base right now. For accurate information, please visit admissions.university.edu or I can create a task for an advisor to contact you."
            }]
        }
