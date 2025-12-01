# Reverse Approach: Create Index First, Then KB via CDK

## The Solution

Your idea is perfect! Instead of trying to create everything via CDK or everything manually, we'll:

1. **Manually create the OpenSearch index** (one-time, 2-3 minutes)
2. **Add KB back to CDK** pointing to the existing index
3. **Deploy stack** - CDK creates the Knowledge Base automatically

This keeps infrastructure-as-code while avoiding the chicken-and-egg problem.

## Step 1: Access OpenSearch Dashboards

The OpenSearch Serverless collection has a built-in web UI for managing indices.

1. **Navigate to the Dashboard**:
   - URL: https://trsvt4rlcapnf4ovn7ba.us-west-2.aoss.amazonaws.com/_dashboards
   - It will redirect you to AWS SSO for authentication
   - Sign in with your AWS credentials

2. **Open Dev Tools**:
   - Once logged in, click "Dev Tools" in the left sidebar (or under the hamburger menu)
   - This opens a console where you can run OpenSearch commands

## Step 2: Create the Index

In the Dev Tools console, paste this command and click the green play button (▶):

```json
PUT /admissions-kb-index
{
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
}
```

**Expected Response**:
```json
{
  "acknowledged": true,
  "shards_acknowledged": true,
  "index": "admissions-kb-index"
}
```

If you see this, the index is created! If you get an error, check:
- You're logged in with the correct AWS account
- The collection name matches (`admissions-kb-collection`)
- You haven't already created an index with this name

## Step 3: Update CDK Stack

Now add the Knowledge Base back to CDK. The code is in `cdk-kb-snippet.ts` - here's how to integrate it:

### 3.1: Add Bedrock Import

At the top of [lib/admissions-agent-stack.ts](lib/admissions-agent-stack.ts#L1), restore:

```typescript
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
```

### 3.2: Replace the KB Comment Section

Find this section (around line 109):

```typescript
// ==================== Bedrock Knowledge Base ====================
// NOTE: Knowledge Base will be created manually via AWS Console after stack deployment
// This avoids CDK/CloudFormation issues with OpenSearch index creation timing

// Grant S3 read access to KB role (for manual KB creation)
knowledgeBaseBucket.grantRead(knowledgeBaseRole);
```

Replace it with:

```typescript
// ==================== Bedrock Knowledge Base ====================
// PREREQUISITE: OpenSearch index "admissions-kb-index" must exist
// Created manually via OpenSearch Dashboards (see CREATE_INDEX_FIRST_APPROACH.md)

const knowledgeBase = new bedrock.CfnKnowledgeBase(this, 'AdmissionsKnowledgeBase', {
  name: 'AdmissionsKnowledgeBase',
  description: 'Knowledge base for Mapua University admissions questions',
  roleArn: knowledgeBaseRole.roleArn,
  knowledgeBaseConfiguration: {
    type: 'VECTOR',
    vectorKnowledgeBaseConfiguration: {
      embeddingModelArn: `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v1`,
    },
  },
  storageConfiguration: {
    type: 'OPENSEARCH_SERVERLESS',
    opensearchServerlessConfiguration: {
      collectionArn: kbCollection.attrArn,
      vectorIndexName: 'admissions-kb-index', // Index created manually in Step 2
      fieldMapping: {
        vectorField: 'vector',
        textField: 'text',
        metadataField: 'metadata',
      },
    },
  },
});
knowledgeBase.addDependency(kbCollection);

// Grant S3 read access to KB role
knowledgeBaseBucket.grantRead(knowledgeBaseRole);

// Create S3 Data Source
const dataSource = new bedrock.CfnDataSource(this, 'KBDataSource', {
  name: 'AdmissionsDocuments',
  description: 'S3 bucket containing Mapua admissions documentation',
  knowledgeBaseId: knowledgeBase.attrKnowledgeBaseId,
  dataSourceConfiguration: {
    type: 'S3',
    s3Configuration: {
      bucketArn: knowledgeBaseBucket.bucketArn,
    },
  },
});
dataSource.addDependency(knowledgeBase);
```

### 3.3: Update Stack Outputs

Replace the OpenSearch-only outputs (around line 289) with:

```typescript
new cdk.CfnOutput(this, 'KnowledgeBaseId', {
  value: knowledgeBase.attrKnowledgeBaseId,
  description: 'Bedrock Knowledge Base ID',
  exportName: 'KnowledgeBaseId',
});

new cdk.CfnOutput(this, 'DataSourceId', {
  value: dataSource.attrDataSourceId,
  description: 'Knowledge Base Data Source ID',
  exportName: 'DataSourceId',
});

new cdk.CfnOutput(this, 'OpenSearchCollectionEndpoint', {
  value: kbCollection.attrCollectionEndpoint,
  description: 'OpenSearch Serverless collection endpoint',
  exportName: 'OpenSearchCollectionEndpoint',
});

new cdk.CfnOutput(this, 'KnowledgeBaseRoleArn', {
  value: knowledgeBaseRole.roleArn,
  description: 'IAM role ARN for Knowledge Base',
  exportName: 'KnowledgeBaseRoleArn',
});
```

## Step 4: Deploy the Updated Stack

```bash
cd Backend/admissions-ai-agent
npx cdk deploy
```

CDK will now successfully create the Knowledge Base because the index already exists!

## Step 5: Sync the Data Source

After deployment completes, sync the Knowledge Base to ingest documents from S3:

```bash
# Get the IDs from CDK outputs
KB_ID="<from-cdk-output>"
DS_ID="<from-cdk-output>"

# Start ingestion
aws bedrock-agent start-ingestion-job \
  --region us-west-2 \
  --knowledge-base-id "$KB_ID" \
  --data-source-id "$DS_ID"
```

Or use the sync script:

```bash
./sync-kb.sh <KB_ID> <DS_ID>
```

## Verification

Check that everything works:

```bash
# Test retrieval
aws bedrock-agent-runtime retrieve \
  --region us-west-2 \
  --knowledge-base-id <KB_ID> \
  --retrieval-query text="What engineering programs does Mapua offer?"
```

## Why This Works

1. **Manual index creation**: Uses the Console's built-in access (no permission issues)
2. **CDK for KB**: Infrastructure remains as code (reproducible)
3. **No chicken-and-egg**: Index exists before KB creation is attempted
4. **One-time manual step**: Only need to create the index once, all future updates are via CDK

## Troubleshooting

### Can't Access OpenSearch Dashboards

If you get "Access Denied" when trying to access the Dashboard:
- Check you're logged into the correct AWS account (756493389182)
- Verify you're using an admin role with OpenSearch Serverless permissions
- Try accessing from a different browser (clear cookies)

### Index Already Exists Error

If you see "resource_already_exists_exception":
- The index was created successfully before
- You can skip Step 2 and go directly to Step 3
- Or delete and recreate: `DELETE /admissions-kb-index` then run the PUT command again

### CDK Deploy Still Fails with "Index Not Found"

- Verify the index name matches exactly: `admissions-kb-index`
- Check the index exists: `GET /admissions-kb-index` in Dev Tools
- Wait a few seconds for propagation, then retry

## Next Steps

After successful deployment:
1. Save KB ID and DS ID from CDK outputs → Update QUICK_REFERENCE.md
2. Create Bedrock Memory
3. Configure AgentCore with KB ID
4. Deploy agent
5. Test end-to-end
