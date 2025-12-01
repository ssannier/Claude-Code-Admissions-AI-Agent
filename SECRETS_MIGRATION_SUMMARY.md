# Secrets Manager Migration Summary

## Overview

Migrated both Salesforce and Twilio credentials from environment variables to AWS Secrets Manager for enhanced security.

---

## Changes Made

### 1. Lambda Functions Updated

#### Form Submission Lambda (`lambda/form-submission/form_submission.py`)
- ✅ Added `get_secret()` function with caching
- ✅ Updated `create_salesforce_lead()` to read from Secrets Manager
- ✅ Replaced environment variables: `SF_USERNAME`, `SF_PASSWORD`, `SF_TOKEN`
- ✅ New environment variable: `SALESFORCE_SECRET_NAME` (default: `admissions-agent/salesforce`)

#### WhatsApp Sender Lambda (`lambda/whatsapp-sender/send_whatsapp_twilio.py`)
- ✅ Added `get_secret()` function with caching
- ✅ Updated `lambda_handler()` to read from Secrets Manager
- ✅ Replaced environment variables: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- ✅ New environment variable: `TWILIO_SECRET_NAME` (default: `admissions-agent/twilio`)

### 2. CDK Stack Updated (`lib/admissions-agent-stack.ts`)

#### Form Submission Lambda
```typescript
environment: {
  SALESFORCE_SECRET_NAME: 'admissions-agent/salesforce',
  AWS_REGION: this.region,
  LOG_LEVEL: 'INFO',
}

// Grant Secrets Manager permissions
formSubmissionLambda.addToRolePolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['secretsmanager:GetSecretValue'],
  resources: [`arn:aws:secretsmanager:${this.region}:${this.account}:secret:admissions-agent/salesforce-*`],
}));
```

#### WhatsApp Sender Lambda
```typescript
environment: {
  TWILIO_SECRET_NAME: 'admissions-agent/twilio',
  MESSAGE_TRACKING_TABLE: messageTrackingTable.tableName,
  AWS_REGION: this.region,
  LOG_LEVEL: 'INFO',
}

// Grant Secrets Manager permissions
whatsappSenderLambda.addToRolePolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['secretsmanager:GetSecretValue'],
  resources: [`arn:aws:secretsmanager:${this.region}:${this.account}:secret:admissions-agent/twilio-*`],
}));
```

### 3. AgentCore Tools Updated

#### `AgentCore/tools/whatsapp_tool.py`
- ✅ Updated default region from `us-east-1` to `us-west-2`

---

## Required Secrets

### 1. Salesforce Secret: `admissions-agent/salesforce`
**Status**: ✅ Created by user

**Required Keys**:
```json
{
  "username": "your-salesforce-email@example.com",
  "password": "your-salesforce-password",
  "token": "your-security-token"
}
```

**Creation Command**:
```bash
aws secretsmanager create-secret \
  --name admissions-agent/salesforce \
  --secret-string '{
    "username":"your-email@example.com",
    "password":"your-password",
    "token":"your-security-token"
  }' \
  --region us-west-2
```

### 2. Twilio Secret: `admissions-agent/twilio`
**Status**: ⏳ Pending user creation

**Required Keys**:
```json
{
  "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "auth_token": "your-auth-token",
  "phone_number": "+14155238886"
}
```

**Creation Command**:
```bash
aws secretsmanager create-secret \
  --name admissions-agent/twilio \
  --secret-string '{
    "account_sid":"ACxxxxxxxx...",
    "auth_token":"your-token",
    "phone_number":"+14155238886"
  }' \
  --region us-west-2
```

---

## Benefits of This Migration

1. **Enhanced Security**:
   - Credentials never stored in environment variables
   - Encrypted at rest and in transit
   - Centralized secret management

2. **Easier Rotation**:
   - Update secrets without redeploying Lambdas
   - Automatic cache invalidation on cold starts
   - Version control for credentials

3. **Audit Trail**:
   - CloudTrail logs all secret access
   - Better compliance with security standards

4. **No Code Changes Needed**:
   - Secrets cached in memory after first retrieval
   - Minimal performance impact
   - Graceful error handling

---

## Deployment Steps

1. **Create Both Secrets** (if not done already):
   - ✅ Salesforce: `admissions-agent/salesforce` (completed)
   - ⏳ Twilio: `admissions-agent/twilio` (pending)

2. **Deploy CDK Stack**:
   ```bash
   cd Backend/admissions-ai-agent
   npx cdk deploy --require-approval never
   ```

3. **Verify Lambda Permissions**:
   ```bash
   # Check Form Submission Lambda
   aws lambda get-function-configuration \
     --function-name admissions-form-submission \
     --region us-west-2 \
     --query "Environment.Variables"

   # Check WhatsApp Sender Lambda
   aws lambda get-function-configuration \
     --function-name admissions-whatsapp-sender \
     --region us-west-2 \
     --query "Environment.Variables"
   ```

4. **Test Integration**:
   - Test form submission (Salesforce)
   - Test WhatsApp message sending (Twilio)
   - Check CloudWatch logs for successful secret retrieval

---

## Rollback Plan (If Needed)

If you need to rollback to environment variables:

1. **Revert CDK Changes**:
   - Restore old environment variables in stack
   - Remove Secrets Manager permissions

2. **Revert Lambda Code**:
   - Comment out `get_secret()` calls
   - Restore `os.environ` lookups

3. **Redeploy**:
   ```bash
   npx cdk deploy --require-approval never
   ```

---

## Testing Checklist

- [ ] Create Twilio account and get credentials
- [ ] Store Twilio credentials in Secrets Manager
- [ ] Deploy CDK stack with updated permissions
- [ ] Test form submission → verify Salesforce Lead created
- [ ] Test WhatsApp message → verify message sent via Twilio
- [ ] Check CloudWatch logs for both Lambdas
- [ ] Verify DynamoDB tracking table has message records
- [ ] Test end-to-end flow: Form → Salesforce → Agent → WhatsApp

---

## Next Steps

1. Follow [TWILIO_SETUP_GUIDE.md](./TWILIO_SETUP_GUIDE.md) to create Twilio account
2. Create `admissions-agent/twilio` secret in AWS Secrets Manager
3. Deploy the updated CDK stack
4. Test both integrations thoroughly
5. Update [DEPLOYMENT_CONFIG.md](./DEPLOYMENT_CONFIG.md) with secret ARNs

---

## Security Notes

⚠️ **Important Reminders**:
- Never commit `.env` files with real credentials
- Rotate secrets regularly (every 90 days recommended)
- Monitor Secrets Manager access via CloudTrail
- Use least-privilege IAM policies
- Delete old environment variables from Lambda Console after migration

✅ **Current Security Posture**:
- Credentials encrypted at rest (AES-256)
- Credentials encrypted in transit (TLS)
- IAM policies restrict access to specific secrets
- CloudTrail logs all secret access
- Secrets cached in Lambda memory (not on disk)
