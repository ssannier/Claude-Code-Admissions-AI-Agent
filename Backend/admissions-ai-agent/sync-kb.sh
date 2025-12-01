#!/bin/bash

# Script to sync Bedrock Knowledge Base after deploying documents to S3
# Usage: ./sync-kb.sh <knowledge-base-id> <data-source-id>

set -e

KNOWLEDGE_BASE_ID=$1
DATA_SOURCE_ID=$2

if [ -z "$KNOWLEDGE_BASE_ID" ] || [ -z "$DATA_SOURCE_ID" ]; then
  echo "Usage: $0 <knowledge-base-id> <data-source-id>"
  echo ""
  echo "To get these IDs from your deployed stack:"
  echo "  aws cloudformation describe-stacks --stack-name AdmissionsAgentStack --query 'Stacks[0].Outputs'"
  exit 1
fi

echo "Starting ingestion job for Knowledge Base..."
echo "Knowledge Base ID: $KNOWLEDGE_BASE_ID"
echo "Data Source ID: $DATA_SOURCE_ID"

INGESTION_JOB_ID=$(aws bedrock-agent start-ingestion-job \
  --knowledge-base-id "$KNOWLEDGE_BASE_ID" \
  --data-source-id "$DATA_SOURCE_ID" \
  --query 'ingestionJob.ingestionJobId' \
  --output text)

echo "Ingestion job started: $INGESTION_JOB_ID"
echo "Waiting for ingestion to complete..."

while true; do
  STATUS=$(aws bedrock-agent get-ingestion-job \
    --knowledge-base-id "$KNOWLEDGE_BASE_ID" \
    --data-source-id "$DATA_SOURCE_ID" \
    --ingestion-job-id "$INGESTION_JOB_ID" \
    --query 'ingestionJob.status' \
    --output text)

  echo "Status: $STATUS"

  if [ "$STATUS" == "COMPLETE" ]; then
    echo "✓ Ingestion completed successfully!"
    break
  elif [ "$STATUS" == "FAILED" ]; then
    echo "✗ Ingestion failed!"
    aws bedrock-agent get-ingestion-job \
      --knowledge-base-id "$KNOWLEDGE_BASE_ID" \
      --data-source-id "$DATA_SOURCE_ID" \
      --ingestion-job-id "$INGESTION_JOB_ID" \
      --query 'ingestionJob.failureReasons'
    exit 1
  fi

  sleep 5
done

echo ""
echo "Knowledge Base is ready to use!"
