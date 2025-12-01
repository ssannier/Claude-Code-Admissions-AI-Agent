# Manual Knowledge Base Creation Guide

## Prerequisites

Your CDK stack has been deployed with the following resources:

- **Region**: us-west-2
- **S3 Bucket**: admissions-agent-kb-756493389182
- **OpenSearch Collection**: https://trsvt4rlcapnf4ovn7ba.us-west-2.aoss.amazonaws.com
- **OpenSearch Collection ARN**: arn:aws:aoss:us-west-2:756493389182:collection/trsvt4rlcapnf4ovn7ba
- **IAM Role ARN**: arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole

## Option 1: AWS Console (Manual Steps)

### Step 1: Navigate to Bedrock
1. Open AWS Console in **us-west-2** region
2. Search for "Amazon Bedrock" in the search bar
3. Click on **Knowledge bases** in the left sidebar

### Step 2: Create Knowledge Base
1. Click **Create knowledge base**
2. **Knowledge base details**:
   - **Name**: `MapuaAdmissionsKB`
   - **Description**: `Knowledge base for Mapua University admissions questions`
   - **IAM role**: Select **Use an existing service role**
   - **Service role ARN**: `arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole`
3. Click **Next**

### Step 3: Configure Data Source
1. **Data source details**:
   - **Name**: `AdmissionsDocuments`
   - **S3 URI**: `s3://admissions-agent-kb-756493389182/`
2. Click **Next**

### Step 4: Select Embeddings Model
1. **Embeddings model**:
   - Model: **Titan Embeddings G1 - Text** (`amazon.titan-embed-text-v1`)
   - Dimensions: 1536 (default)
2. Click **Next**

### Step 5: Configure Vector Store
1. **Vector database**: Select **Amazon OpenSearch Serverless**
2. **Choose an existing collection**:
   - Collection ARN: `arn:aws:aoss:us-west-2:756493389182:collection/trsvt4rlcapnf4ovn7ba`
   - **IMPORTANT**: You'll need to create an index in this collection first
3. **Vector index name**: `admissions-kb-index`
4. **Vector field**: `vector`
5. **Text field**: `text`
6. **Metadata field**: `metadata`
7. Click **Next**

### Step 6: Review and Create
1. Review all settings
2. Click **Create knowledge base**
3. **IMPORTANT**: After creation, click **Sync** to ingest the documents from S3

### Step 7: Save the Knowledge Base ID
After creation, you'll see a Knowledge Base ID (format: `XXXXXXXXXX`). Save this ID - you'll need it for:
- AgentCore configuration
- Testing queries

## Option 2: AWS CLI (Automated - RECOMMENDED)

This script automates the entire process:

```bash
#!/bin/bash
set -e

REGION="us-west-2"
KB_NAME="MapuaAdmissionsKB"
ROLE_ARN="arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole"
S3_BUCKET="admissions-agent-kb-756493389182"
COLLECTION_ARN="arn:aws:aoss:us-west-2:756493389182:collection/trsvt4rlcapnf4ovn7ba"
INDEX_NAME="admissions-kb-index"

echo "Creating Bedrock Knowledge Base: $KB_NAME"

# Create the Knowledge Base
KB_RESPONSE=$(aws bedrock-agent create-knowledge-base \
  --region "$REGION" \
  --name "$KB_NAME" \
  --description "Knowledge base for Mapua University admissions questions" \
  --role-arn "$ROLE_ARN" \
  --knowledge-base-configuration "{
    \"type\": \"VECTOR\",
    \"vectorKnowledgeBaseConfiguration\": {
      \"embeddingModelArn\": \"arn:aws:bedrock:$REGION::foundation-model/amazon.titan-embed-text-v1\"
    }
  }" \
  --storage-configuration "{
    \"type\": \"OPENSEARCH_SERVERLESS\",
    \"opensearchServerlessConfiguration\": {
      \"collectionArn\": \"$COLLECTION_ARN\",
      \"vectorIndexName\": \"$INDEX_NAME\",
      \"fieldMapping\": {
        \"vectorField\": \"vector\",
        \"textField\": \"text\",
        \"metadataField\": \"metadata\"
      }
    }
  }")

KB_ID=$(echo $KB_RESPONSE | jq -r '.knowledgeBase.knowledgeBaseId')
echo "✓ Knowledge Base created: $KB_ID"

# Create the S3 Data Source
DS_RESPONSE=$(aws bedrock-agent create-data-source \
  --region "$REGION" \
  --knowledge-base-id "$KB_ID" \
  --name "AdmissionsDocuments" \
  --description "S3 bucket containing Mapua admissions documentation" \
  --data-source-configuration "{
    \"type\": \"S3\",
    \"s3Configuration\": {
      \"bucketArn\": \"arn:aws:s3:::$S3_BUCKET\"
    }
  }")

DS_ID=$(echo $DS_RESPONSE | jq -r '.dataSource.dataSourceId')
echo "✓ Data Source created: $DS_ID"

# Start ingestion job
echo "Starting ingestion job..."
INGESTION_RESPONSE=$(aws bedrock-agent start-ingestion-job \
  --region "$REGION" \
  --knowledge-base-id "$KB_ID" \
  --data-source-id "$DS_ID")

INGESTION_JOB_ID=$(echo $INGESTION_RESPONSE | jq -r '.ingestionJob.ingestionJobId')
echo "✓ Ingestion job started: $INGESTION_JOB_ID"

echo ""
echo "============================================"
echo "Knowledge Base Details"
echo "============================================"
echo "Knowledge Base ID: $KB_ID"
echo "Data Source ID: $DS_ID"
echo "Ingestion Job ID: $INGESTION_JOB_ID"
echo "Region: $REGION"
echo ""
echo "Save these IDs for later use!"
echo ""
echo "To check ingestion status:"
echo "aws bedrock-agent get-ingestion-job \\"
echo "  --region $REGION \\"
echo "  --knowledge-base-id $KB_ID \\"
echo "  --data-source-id $DS_ID \\"
echo "  --ingestion-job-id $INGESTION_JOB_ID"
```

Save this as `create-kb.sh` and run:
```bash
chmod +x create-kb.sh
./create-kb.sh
```

## Verification

After creation and sync, verify the Knowledge Base:

```bash
# Check Knowledge Base status
aws bedrock-agent get-knowledge-base \
  --region us-west-2 \
  --knowledge-base-id <YOUR_KB_ID>

# Check ingestion job status
aws bedrock-agent list-ingestion-jobs \
  --region us-west-2 \
  --knowledge-base-id <YOUR_KB_ID> \
  --data-source-id <YOUR_DS_ID>

# Test a query
aws bedrock-agent-runtime retrieve \
  --region us-west-2 \
  --knowledge-base-id <YOUR_KB_ID> \
  --retrieval-query "text=What engineering programs does Mapua offer?"
```

## Common Issues

### Issue: "Index does not exist" error
**Solution**: The index is automatically created during the first sync. If you see this error, wait for the ingestion job to complete.

### Issue: "Access Denied" when querying
**Solution**: Verify the IAM role has `aoss:APIAccessAll` permission on the OpenSearch collection.

### Issue: Sync fails with S3 permission error
**Solution**: Verify the IAM role has `s3:GetObject` and `s3:ListBucket` permissions on the S3 bucket.

## Next Steps

After the Knowledge Base is created and synced:

1. Save the Knowledge Base ID
2. Create Bedrock Memory for conversation history
3. Configure AgentCore with the Knowledge Base ID
4. Test retrieval queries
5. Deploy the agent
