#!/bin/bash
# Script to create OpenSearch index before Knowledge Base creation
set -e

REGION="us-west-2"
COLLECTION_ENDPOINT="https://trsvt4rlcapnf4ovn7ba.us-west-2.aoss.amazonaws.com"
INDEX_NAME="admissions-kb-index"

echo "Creating OpenSearch Serverless index: $INDEX_NAME"
echo "Collection: $COLLECTION_ENDPOINT"
echo ""

# Create the index with proper mappings for Bedrock Knowledge Base
curl -X PUT "$COLLECTION_ENDPOINT/$INDEX_NAME" \
  --aws-sigv4 "aws:amz:$REGION:aoss" \
  --user "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "index": {
        "knn": true,
        "knn.algo_param.ef_search": 512
      }
    },
    "mappings": {
      "properties": {
        "vector": {
          "type": "knn_vector",
          "dimension": 1536,
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
  }'

echo ""
echo "✓ Index created successfully!"
echo ""
echo "You can now create the Knowledge Base using create-kb.sh"
