# Quick Reference - Deployed Resources

## AWS Stack Outputs (from deployment)

```
Account: 756493389182
Region: us-west-2
Stack: AdmissionsAgentStack
```

### API Endpoints
- **Form Submission API**: https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod/submit
- **Agent Proxy (SSE)**: https://56esu4j6ukmbjfwzqoml7jsjvq0uwrdw.lambda-url.us-west-2.on.aws/

### Storage Resources
- **S3 Knowledge Base Bucket**: admissions-agent-kb-756493389182
- **DynamoDB Sessions Table**: WhatsappSessions
- **DynamoDB Message Tracking**: WhatsAppMessageTracking
- **OpenSearch Collection**: admissions-kb-collection
- **OpenSearch Endpoint**: https://trsvt4rlcapnf4ovn7ba.us-west-2.aoss.amazonaws.com

### Compute Resources
- **ECR Repository**: 756493389182.dkr.ecr.us-west-2.amazonaws.com/admissions-agent
- **Agent Execution Role**: arn:aws:iam::756493389182:role/AdmissionsAgentExecutionRole
- **Knowledge Base Role**: arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole

### Messaging
- **SQS Queue**: https://sqs.us-west-2.amazonaws.com/756493389182/twilio-whatsapp-queue

## Next Steps for Testing

### 1. Create Bedrock Knowledge Base (via AWS Console)

**Status**: ⏳ IN PROGRESS

**Go to**: https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/knowledge-bases

**Detailed Instructions**: See [KNOWLEDGE_BASE_INSTRUCTIONS.md](Backend/admissions-ai-agent/KNOWLEDGE_BASE_INSTRUCTIONS.md)

**Configuration Summary**:
- Name: `AdmissionsKnowledgeBase`
- IAM Role: `arn:aws:iam::756493389182:role/AdmissionsKnowledgeBaseRole` (already created)
- S3 Data Source: `s3://admissions-agent-kb-756493389182/`
- OpenSearch Collection: `admissions-kb-collection` (already created)
- Embeddings: Titan Embeddings G1 - Text
- Vector Index: Let AWS create automatically

**After Creation**:
1. Click "Sync" to ingest documents
2. Save the Knowledge Base ID below:

**Knowledge Base ID**: `<PASTE_ID_HERE>`
**Data Source ID**: `<PASTE_ID_HERE>`

### 2. Create Bedrock Memory

```bash
aws bedrock-agent create-memory \
  --memory-name "AdmissionsMemory" \
  --memory-configuration '{"type": "SESSION_SUMMARY"}' \
  --region us-west-2
```

Save the Memory ID from the output.

**Memory ID**: `<PASTE_ID_HERE>`

### 3. Update Frontend Configuration

Edit `Frontend/admissions-chat/.env.local`:

```env
NEXT_PUBLIC_API_URL=https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod
NEXT_PUBLIC_AGENT_PROXY_URL=https://56esu4j6ukmbjfwzqoml7jsjvq0uwrdw.lambda-url.us-west-2.on.aws
```

### 4. Test Form Submission

```bash
cd Frontend/admissions-chat
npm run dev
```

Open http://localhost:3000 and test:
1. Fill out inquiry form
2. Submit and verify redirect to chat
3. Check DynamoDB for session creation:
   ```bash
   aws dynamodb scan --table-name WhatsappSessions --max-items 5
   ```

### 5. Configure AgentCore (After KB is ready)

```bash
cd Backend/admissions-ai-agent/AgentCore

# Create .env file
cat > .env << EOF
AWS_REGION=us-west-2
KNOWLEDGE_BASE_ID=<your-kb-id-here>
MEMORY_ID=<your-memory-id-here>

# Disable external integrations for testing
ENABLE_SALESFORCE=false
ENABLE_TWILIO=false

AGENT_ID=<will-be-created>
AGENT_ALIAS_ID=TSTALIASID
EOF

# Configure agent
npx agentcore configure
```

**During configuration**:
- Model: Claude Sonnet 4.5
- Skip Salesforce tool (for now)
- Skip Twilio tool (for now)
- Enable Knowledge Base tool with your KB ID
- Enable Memory with your Memory ID

### 6. Deploy Agent

```bash
# After configuration
npx agentcore deploy
```

Save the Agent Runtime ARN from the output.

### 7. Update Agent Proxy Lambda

Update the `AGENT_RUNTIME_ARN` environment variable in the Agent Proxy Lambda:

```bash
aws lambda update-function-configuration \\
  --function-name admissions-agent-proxy \\
  --environment Variables="{AGENT_RUNTIME_ARN=<your-agent-runtime-arn>,LOG_LEVEL=INFO}"
```

## Verification Commands

### Check Infrastructure
```bash
# S3 bucket contents
aws s3 ls s3://admissions-agent-kb-756493389182/

# DynamoDB tables
aws dynamodb list-tables | grep -E "Whatsapp|MessageTracking"

# Lambda functions
aws lambda list-functions | grep admissions

# API Gateway
aws apigateway get-rest-apis --query 'items[?name==`Admissions Form API`]'
```

### Check Knowledge Base Status
```bash
# List knowledge bases
aws bedrock-agent list-knowledge-bases

# Get specific KB details
aws bedrock-agent get-knowledge-base --knowledge-base-id <kb-id>

# Check data source sync status
aws bedrock-agent list-ingestion-jobs \\
  --knowledge-base-id <kb-id> \\
  --data-source-id <data-source-id>
```

### Monitor Logs
```bash
# Form submission Lambda
aws logs tail /aws/lambda/admissions-form-submission --follow

# Agent Proxy Lambda
aws logs tail /aws/lambda/admissions-agent-proxy --follow

# WhatsApp Sender Lambda
aws logs tail /aws/lambda/admissions-whatsapp-sender --follow
```

## Test Knowledge Base Document

A test document has already been uploaded to S3:
- **Location**: `s3://admissions-agent-kb-756493389182/test-kb-doc.txt`
- **Size**: 6.4 KB
- **Contains**: Mapua University admissions information (programs, requirements, tuition, contact info)

## Troubleshooting

### Issue: Knowledge Base sync fails
**Solution**: Check IAM role permissions for the KB role

### Issue: Form submission fails with CORS error
**Solution**: Verify API Gateway CORS settings allow your frontend origin

### Issue: Agent doesn't respond
**Solution**:
1. Check Agent Runtime ARN is correctly set in Agent Proxy Lambda
2. Verify Agent is deployed: `npx agentcore status`
3. Check CloudWatch logs for errors

### Issue: Memory not persisting
**Solution**: Verify Memory ID is correct in AgentCore configuration

## Cost Monitoring

Set up AWS Budget Alert:
```bash
aws budgets create-budget \\
  --account-id 756493389182 \\
  --budget file://budget-config.json \\
  --notifications-with-subscribers file://notifications.json
```

**Estimated testing costs**: $5-20/month
- Lambda: Free tier (1M requests/month)
- DynamoDB: Free tier (25GB)
- OpenSearch Serverless: ~$0.24/OCU-hour
- Bedrock: ~$0.002/request

## Resources for Reference

- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Testing Without KB**: [TESTING_WITHOUT_KB.md](TESTING_WITHOUT_KB.md)
- **Project Instructions**: [CLAUDE.md](CLAUDE.md)
- **CDK Stack**: [Backend/admissions-ai-agent/lib/admissions-agent-stack.ts](Backend/admissions-ai-agent/lib/admissions-agent-stack.ts)
