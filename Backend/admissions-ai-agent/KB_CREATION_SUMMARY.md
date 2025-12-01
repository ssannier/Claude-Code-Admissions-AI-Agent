# Knowledge Base Creation - Ready to Go

## Current Status

✅ **Infrastructure Deployed** - All AWS resources are ready in us-west-2
⏳ **Creating Knowledge Base** - User is creating "AdmissionsKnowledgeBase" via Console

## What's Already Set Up

### 1. OpenSearch Serverless Collection
- **Name**: `admissions-kb-collection`
- **Endpoint**: https://trsvt4rlcapnf4ovn7ba.us-west-2.aoss.amazonaws.com
- **ARN**: arn:aws:aoss:us-west-2:756493389182:collection/trsvt4rlcapnf4ovn7ba
- **Status**: Active and ready

### 2. IAM Role for Knowledge Base
- **Role Name**: `AdmissionsKnowledgeBaseRole`
- **ARN**: arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole
- **Permissions**:
  - ✅ S3 read access to `admissions-agent-kb-756493389182`
  - ✅ OpenSearch Serverless full API access
  - ✅ Bedrock InvokeModel for Titan Embeddings

### 3. S3 Bucket with Test Data
- **Bucket**: `admissions-agent-kb-756493389182`
- **Test Document**: `test-kb-doc.txt` (6.4 KB, Mapua admissions info)
- **Status**: Ready for ingestion

### 4. Security Policies
- **Encryption Policy**: `admissions-kb-encryption` ✅
- **Network Policy**: `admissions-kb-network` ✅ (allows public access)
- **Data Access Policy**: `admissions-kb-access` ✅ (grants KB role permissions)

## Knowledge Base Configuration

Use these exact values when creating the KB in the AWS Console:

| Field | Value |
|-------|-------|
| **Name** | `AdmissionsKnowledgeBase` |
| **Description** | Knowledge base for Mapua University admissions questions |
| **IAM Role** | Use existing: `arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole` |
| **S3 URI** | `s3://admissions-agent-kb-756493389182/` |
| **Data Source Name** | `AdmissionsDocuments` |
| **Embeddings Model** | Titan Embeddings G1 - Text (`amazon.titan-embed-text-v1`) |
| **Vector Database** | Amazon OpenSearch Serverless |
| **Collection** | Choose existing: `admissions-kb-collection` |
| **Vector Index** | **Let AWS create a new vector index** (CRITICAL!) |

## After KB Creation - Next Steps

Once you've created the Knowledge Base and synced it:

### 1. Save the IDs
```bash
# Update these in QUICK_REFERENCE.md
Knowledge Base ID: <from console>
Data Source ID: <from console>
```

### 2. Create Bedrock Memory
```bash
aws bedrock-agent create-memory \
  --memory-name "AdmissionsMemory" \
  --memory-configuration '{"type": "SESSION_SUMMARY"}' \
  --region us-west-2
```

### 3. Configure AgentCore
```bash
cd Backend/admissions-ai-agent/AgentCore

# Create .env with the KB ID and Memory ID
cat > .env << EOF
AWS_REGION=us-west-2
KNOWLEDGE_BASE_ID=<from-step-1>
MEMORY_ID=<from-step-2>
ENABLE_SALESFORCE=false
ENABLE_TWILIO=false
EOF

# Configure and deploy
npx agentcore configure
npx agentcore deploy
```

### 4. Update Frontend
```bash
cd Frontend/admissions-chat

# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod
NEXT_PUBLIC_AGENT_PROXY_URL=https://56esu4j6ukmbjfwzqoml7jsjvq0uwrdw.lambda-url.us-west-2.on.aws
EOF

# Test locally
npm run dev
```

### 5. Update Agent Proxy Lambda
After deploying AgentCore, update the Lambda with the Agent Runtime ARN:

```bash
aws lambda update-function-configuration \
  --region us-west-2 \
  --function-name admissions-agent-proxy \
  --environment Variables="{AGENT_RUNTIME_ARN=<your-agent-runtime-arn>,LOG_LEVEL=INFO}"
```

## Verification Commands

### Check KB Status
```bash
aws bedrock-agent get-knowledge-base \
  --region us-west-2 \
  --knowledge-base-id <KB_ID>
```

### Check Ingestion Progress
```bash
aws bedrock-agent list-ingestion-jobs \
  --region us-west-2 \
  --knowledge-base-id <KB_ID> \
  --data-source-id <DS_ID>
```

### Test Retrieval
```bash
aws bedrock-agent-runtime retrieve \
  --region us-west-2 \
  --knowledge-base-id <KB_ID> \
  --retrieval-query text="What engineering programs does Mapua offer?"
```

## Troubleshooting

### If KB creation fails with "index does not exist"
This shouldn't happen if you select "Let AWS create a new vector index". If it does:
1. Delete the failed KB
2. Ensure you selected "Let AWS create" (not "Use existing")
3. Try again

### If sync fails with permission errors
Check the IAM role has:
- `s3:GetObject` on the bucket
- `s3:ListBucket` on the bucket
- `aoss:APIAccessAll` on the collection

### If retrieval returns no results
1. Verify sync job completed successfully
2. Check the document was uploaded to S3
3. Test with a simple query like "What is Mapua?"

## Reference Documents

- **Detailed Instructions**: [KNOWLEDGE_BASE_INSTRUCTIONS.md](./KNOWLEDGE_BASE_INSTRUCTIONS.md)
- **Quick Reference**: [QUICK_REFERENCE.md](../../QUICK_REFERENCE.md)
- **Stack Definition**: [lib/admissions-agent-stack.ts](./lib/admissions-agent-stack.ts)
