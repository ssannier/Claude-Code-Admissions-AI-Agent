"""
Knowledge Base Search Tool

Searches admissions documentation using Amazon Bedrock Knowledge Base with vector search.
Properties 8-11: Knowledge Base retrieval with relevance scoring and source attribution
"""

import os
import logging
from typing import Dict, Any, List
from strands import tool
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_bedrock_agent_runtime_client():
    """Get Bedrock Agent Runtime client instance."""
    return boto3.client(
        'bedrock-agent-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )


def retrieve_from_knowledge_base(
    query: str,
    knowledge_base_id: str,
    number_of_results: int = 5,
    score_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant documents from Bedrock Knowledge Base using vector search.

    Property 8: Factual questions trigger knowledge base search
    Property 9: Results filtered by relevance score threshold (0.5)

    Args:
        query: Search query text
        knowledge_base_id: Bedrock Knowledge Base ID
        number_of_results: Maximum results to return
        score_threshold: Minimum relevance score (0.0-1.0)

    Returns:
        List of relevant documents with content, scores, and metadata
    """
    try:
        client = get_bedrock_agent_runtime_client()

        response = client.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': number_of_results
                }
            }
        )

        results = []
        for result in response.get('retrievalResults', []):
            score = result.get('score', 0.0)

            # Property 9: Filter by relevance score >= 0.5
            if score >= score_threshold:
                content = result.get('content', {}).get('text', '')
                location = result.get('location', {})

                # Extract source information
                s3_location = location.get('s3Location', {})
                uri = s3_location.get('uri', '')

                # Parse document name and URL from S3 URI
                doc_name = uri.split('/')[-1] if uri else 'Unknown Document'

                results.append({
                    'content': content,
                    'score': score,
                    'document_name': doc_name,
                    'uri': uri,
                    'metadata': result.get('metadata', {})
                })

        return results

    except ClientError as e:
        logger.error(f"Bedrock Knowledge Base error: {str(e)}", exc_info=True)
        return []

    except Exception as e:
        logger.error(f"Error retrieving from knowledge base: {str(e)}", exc_info=True)
        return []


@tool
def retrieve_university_info(
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

    Properties Implemented:
    - Property 8: Factual questions trigger knowledge base search
    - Property 9: KB results filtered by relevance score >= 0.5
    - Property 10: KB responses include source attribution (document names and URLs)
    - Property 11: KB search displays tool indicator (via tool_use event)

    Args:
        query: Search query describing what information is needed
               (e.g., "undergraduate admission requirements", "graduate program deadlines")
        topic: Topic category - "requirements", "programs", "deadlines", "financial",
               "campus", or "general" (default: "general")

    Returns:
        Relevant information from the knowledge base with sources and relevance scores
    """
    try:
        # Get Knowledge Base ID from environment
        knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')

        if not knowledge_base_id:
            logger.warning("KNOWLEDGE_BASE_ID not configured, using fallback message")
            return {
                "status": "error",
                "content": [{
                    "text": "The knowledge base is not currently configured. Please visit admissions.university.edu or let me connect you with a human advisor."
                }]
            }

        # Retrieve from Bedrock Knowledge Base
        results = retrieve_from_knowledge_base(
            query=query,
            knowledge_base_id=knowledge_base_id,
            number_of_results=5,
            score_threshold=0.5  # Property 9: Minimum relevance score
        )

        if not results:
            return {
                "status": "success",
                "content": [{
                    "text": "I couldn't find specific information about that in our knowledge base. Let me create a task for a human advisor to provide you with accurate details, or you can visit our website at admissions.university.edu."
                }]
            }

        # Format results with source attribution (Property 10)
        response_text = f"Based on our admissions documentation:\n\n"

        for i, result in enumerate(results, 1):
            doc_name = result['document_name']
            content = result['content'][:500]  # First 500 chars
            score = result['score']
            uri = result['uri']

            response_text += f"**Source {i}: {doc_name}** (Relevance: {score:.2f})\n"
            response_text += f"{content}\n\n"

            if len(result['content']) > 500:
                response_text += "...\n\n"

            # Add URL if available
            if uri:
                response_text += f"_[View full document]({uri})_\n\n"

        response_text += f"*Found {len(results)} relevant document(s) with relevance scores >= 0.5. For complete details, please visit our admissions website or contact an advisor.*"

        return {
            "status": "success",
            "content": [{"text": response_text}],
            "sources": [
                {
                    "document_name": r['document_name'],
                    "uri": r['uri'],
                    "score": r['score']
                }
                for r in results
            ],
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
