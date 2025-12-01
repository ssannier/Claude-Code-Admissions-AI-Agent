#!/usr/bin/env python3
"""
Script to create OpenSearch Serverless index for Bedrock Knowledge Base.
This must be done before creating the Knowledge Base.
"""
import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Configuration
REGION = "us-west-2"
COLLECTION_ENDPOINT = "trsvt4rlcapnf4ovn7ba.us-west-2.aoss.amazonaws.com"
INDEX_NAME = "admissions-kb-index"

# AWS credentials
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, REGION, 'aoss')

# OpenSearch client
client = OpenSearch(
    hosts=[{'host': COLLECTION_ENDPOINT, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    pool_maxsize=20,
    timeout=300
)

print(f"Creating OpenSearch index: {INDEX_NAME}")
print(f"Collection: {COLLECTION_ENDPOINT}")
print("")

# Index configuration for Bedrock Knowledge Base
index_body = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 512
        }
    },
    "mappings": {
        "properties": {
            "vector": {
                "type": "knn_vector",
                "dimension": 1536,  # Titan Embeddings G1 dimension
                "method": {
                    "name": "hnsw",
                    "engine": "faiss",
                    "parameters": {
                        "ef_construction": 512,
                        "m": 16
                    }
                }
            },
            "text": {
                "type": "text"
            },
            "metadata": {
                "type": "object"
            }
        }
    }
}

try:
    # Check if index already exists
    if client.indices.exists(index=INDEX_NAME):
        print(f"[WARNING] Index '{INDEX_NAME}' already exists")
        print("Deleting existing index...")
        client.indices.delete(index=INDEX_NAME)
        print("[OK] Existing index deleted")

    # Create the index
    response = client.indices.create(index=INDEX_NAME, body=index_body)
    print(f"[OK] Index '{INDEX_NAME}' created successfully!")
    print("")
    print("Index configuration:")
    print(json.dumps(index_body, indent=2))
    print("")
    print("[OK] You can now create the Knowledge Base using create-kb.sh")

except Exception as e:
    print(f"[ERROR] Error creating index: {str(e)}")
    print("")
    print("Troubleshooting:")
    print("1. Verify your AWS credentials have access to OpenSearch Serverless")
    print("2. Check that the data access policy allows index creation")
    print("3. Ensure the collection endpoint is correct")
    exit(1)
