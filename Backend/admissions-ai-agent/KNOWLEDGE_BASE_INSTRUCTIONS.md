# Knowledge Base Creation - Issue and Solution

## Problem

We've encountered the OpenSearch index chicken-and-egg problem:

1. **CDK/CloudFormation approach**: Cannot create Knowledge Base via CDK because it validates that the OpenSearch index exists, but the index is only created during the first data source sync.

2. **Python/CLI script approach**: Cannot create the index programmatically because the data access policy only grants permissions to the Knowledge Base role, not to admin users.

3. **Updating data access policy**: Would require redeploying the CDK stack, but then we're back to problem #1.

## Recommended Solution: AWS Console Creation

The AWS Console has special handling for this case and can create the Knowledge Base and index together. Follow these steps:

### Step 1: Open Bedrock Console

1. Navigate to: https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/knowledge-bases
2. Click **"Create knowledge base"**

### Step 2: Configure Knowledge Base Details

- **Name**: `AdmissionsKnowledgeBase`
- **Description**: `Knowledge base for Mapua University admissions questions`
- **IAM role**:
  - Select **"Use an existing service role"**
  - **Service role ARN**: `arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole`
- Click **Next**

### Step 3: Configure Data Source

- **Data source name**: `AdmissionsDocuments`
- **S3 URI**: `s3://admissions-agent-kb-756493389182/`
- Click **Next**

### Step 4: Select Embeddings Model

- **Embeddings model**: **Titan Embeddings G1 - Text** (`amazon.titan-embed-text-v1`)
- Click **Next**

### Step 5: Configure Vector Store (CRITICAL)

- **Vector database**: Select **"Amazon OpenSearch Serverless"**
- **Collection selection**:
  - Select **"Choose an existing collection"**
  - Find collection: `admissions-kb-collection`
  - Collection ARN: `arn:aws:aoss:us-west-2:756493389182:collection/trsvt4rlcapnf4ovn7ba`
- **Vector index**:
  - Select **"Let AWS create a new vector index"** (NOT "Use an existing vector index")
  - The console will automatically generate an index name like `bedrock-knowledge-base-default-index`
- Click **Next**

### Step 6: Review and Create

1. Review all settings
2. Click **"Create knowledge base"**
3. AWS will create both the Knowledge Base and the OpenSearch index
4. After creation, click **"Sync"** to ingest documents from S3

### Step 7: Save the IDs

After successful creation, note these values:

- **Knowledge Base ID**: (format: `XXXXXXXXXX`) - shown in the KB details
- **Data Source ID**: (shown in Data sources tab)

You'll need the Knowledge Base ID for:
1. AgentCore configuration (`AgentCore/.env`)
2. Testing retrieval queries
3. Future data syncs

## Verification

After the sync completes, test the Knowledge Base:

```bash
aws bedrock-agent-runtime retrieve \
  --region us-west-2 \
  --knowledge-base-id <YOUR_KB_ID> \
  --retrieval-query text="What engineering programs does Mapua offer?"
```

## Why Console Works But CLI Doesn't

The AWS Console has special backend logic that:
1. Creates the OpenSearch index on-demand when you select "Let AWS create a new vector index"
2. Temporarily elevates permissions to allow index creation
3. Then creates the Knowledge Base resource pointing to the new index

This workflow is not available via CloudFormation or direct AWS CLI commands, which is why we must use the Console for initial setup.

## Next Steps After KB Creation

1. Update `QUICK_REFERENCE.md` with the actual Knowledge Base ID
2. Update `Backend/admissions-ai-agent/AgentCore/.env` with the Knowledge Base ID
3. Configure and deploy AgentCore
4. Test end-to-end with the frontend

## Alternative Workaround (Advanced)

If you absolutely need to automate this, you could:
1. Create a Lambda function that acts as a Custom Resource in CDK
2. Have that Lambda create the index using the Knowledge Base role's credentials (via STS AssumeRole)
3. Then create the Knowledge Base in CDK

However, this is significantly more complex than just using the Console once.
