#!/bin/bash
# Script to create Bedrock Knowledge Base using AWS CLI with auto-generated index
set -e

REGION="us-west-2"
KB_NAME="AdmissionsKnowledgeBase"
ROLE_ARN="arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole"
S3_BUCKET="admissions-agent-kb-756493389182"
COLLECTION_ARN="arn:aws:aoss:us-west-2:756493389182:collection/trsvt4rlcapnf4ovn7ba"

# Use a timestamp-based index name to ensure uniqueness
INDEX_NAME="bedrock-kb-$(date +%s)"

echo "Creating Bedrock Knowledge Base: $KB_NAME in $REGION"
echo "Using auto-generated index name: $INDEX_NAME"
echo ""

# First, create the index using the Knowledge Base role's credentials
echo "Step 1: Creating OpenSearch index as Knowledge Base role..."
# Note: This won't work directly as we can't assume the role easily
# We'll let the KB creation handle it

# Create the Knowledge Base without pre-creating the index
echo "Step 1: Creating Knowledge Base..."
KB_RESPONSE=$(aws bedrock-agent create-knowledge-base \
  --region "$REGION" \
  --name "$KB_NAME" \
  --description "Knowledge base for Mapua University admissions questions" \
  --role-arn "$ROLE_ARN" \
  --knowledge-base-configuration '{
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
      "embeddingModelArn": "arn:aws:bedrock:'"$REGION"'::foundation-model/amazon.titan-embed-text-v1"
    }
  }' \
  --storage-configuration '{
    "type": "OPENSEARCH_SERVERLESS",
    "opensearchServerlessConfiguration": {
      "collectionArn": "'"$COLLECTION_ARN"'",
      "vectorIndexName": "'"$INDEX_NAME"'",
      "fieldMapping": {
        "vectorField": "vector",
        "textField": "text",
        "metadataField": "metadata"
      }
    }
  }' 2>&1)

if [ $? -ne 0 ]; then
  echo "✗ Knowledge Base creation failed!"
  echo "$KB_RESPONSE"
  exit 1
fi

KB_ID=$(echo "$KB_RESPONSE" | jq -r '.knowledgeBase.knowledgeBaseId')
echo "✓ Knowledge Base created successfully!"
echo "  Knowledge Base ID: $KB_ID"
echo ""

# Create the S3 Data Source
echo "Step 2: Creating S3 Data Source..."
DS_RESPONSE=$(aws bedrock-agent create-data-source \
  --region "$REGION" \
  --knowledge-base-id "$KB_ID" \
  --name "AdmissionsDocuments" \
  --description "S3 bucket containing Mapua admissions documentation" \
  --data-source-configuration '{
    "type": "S3",
    "s3Configuration": {
      "bucketArn": "arn:aws:s3:::'"$S3_BUCKET"'"
    }
  }')

DS_ID=$(echo "$DS_RESPONSE" | jq -r '.dataSource.dataSourceId')
echo "✓ Data Source created successfully!"
echo "  Data Source ID: $DS_ID"
echo ""

# Start ingestion job
echo "Step 3: Starting ingestion job to sync documents from S3..."
INGESTION_RESPONSE=$(aws bedrock-agent start-ingestion-job \
  --region "$REGION" \
  --knowledge-base-id "$KB_ID" \
  --data-source-id "$DS_ID")

INGESTION_JOB_ID=$(echo "$INGESTION_RESPONSE" | jq -r '.ingestionJob.ingestionJobId')
echo "✓ Ingestion job started!"
echo "  Ingestion Job ID: $INGESTION_JOB_ID"
echo ""

echo "============================================"
echo "Knowledge Base Created Successfully!"
echo "============================================"
echo ""
echo "SAVE THESE IDs:"
echo "  Knowledge Base ID: $KB_ID"
echo "  Data Source ID: $DS_ID"
echo "  Ingestion Job ID: $INGESTION_JOB_ID"
echo "  Vector Index Name: $INDEX_NAME"
echo "  Region: $REGION"
echo ""
echo "Next steps:"
echo "  1. Monitor ingestion status (see command below)"
echo "  2. Once ingestion completes, test retrieval"
echo "  3. Use Knowledge Base ID in AgentCore configuration"
echo ""
echo "To check ingestion status:"
echo "  aws bedrock-agent get-ingestion-job \\"
echo "    --region $REGION \\"
echo "    --knowledge-base-id $KB_ID \\"
echo "    --data-source-id $DS_ID \\"
echo "    --ingestion-job-id $INGESTION_JOB_ID"
echo ""
