# Twilio WhatsApp Setup Guide for Admissions Agent

## Step 1: Create Twilio Account

1. **Sign up for Twilio Trial**:
   - Go to: https://www.twilio.com/try-twilio
   - Click **"Sign up and start building"**
   - Fill in your details:
     - First name, Last name
     - Email address
     - Password
   - Click **"Start your free trial"**

2. **Verify Your Email and Phone**:
   - Check your email for verification link
   - Verify your phone number (you'll receive a code via SMS)

3. **Complete Onboarding**:
   - Answer the setup questions:
     - Which Twilio product? → **"Messaging"**
     - What do you plan to build? → **"Alerts & Notifications"**
     - How do you want to build? → **"With code"**
     - What's your preferred language? → **"Python"**
   - Click through to Dashboard

---

## Step 2: Get Your Account Credentials

1. **Find Your Account SID and Auth Token**:
   - On the Twilio Console Dashboard: https://console.twilio.com/
   - Look for the **"Account Info"** section
   - You'll see:
     - **Account SID** (starts with "AC...") - click to copy
     - **Auth Token** - click the eye icon to reveal, then copy

   ```
   Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Auth Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

2. **Save These Credentials Temporarily**:
   - Keep them handy for the AWS Secrets Manager step

---

## Step 3: Set Up WhatsApp Sandbox

Twilio provides a free WhatsApp sandbox for testing (no approval needed).

1. **Navigate to WhatsApp Sandbox**:
   - In left sidebar: **Messaging** → **Try it out** → **Send a WhatsApp message**
   - OR go directly to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

2. **Get Your Sandbox Number**:
   - You'll see a sandbox phone number like: **+1 415 523 8886**
   - This is your Twilio WhatsApp number - save it!

3. **Join the Sandbox from Your Phone**:
   - Open WhatsApp on your mobile device
   - Send a message to the Twilio sandbox number with the exact join code shown
   - Example: Send `join yellow-tiger` to `+1 415 523 8886`
   - You'll receive a confirmation message: "Awesome! You are all set."

4. **Verify Multiple Test Numbers** (if needed):
   - In trial mode, you can only send to verified numbers
   - Go to: **Phone Numbers** → **Manage** → **Verified Caller IDs**
   - Click **"Add a new Caller ID"**
   - Enter the phone number you want to test with
   - Complete verification via SMS code

---

## Step 4: Store Credentials in AWS Secrets Manager

Now let's securely store the Twilio credentials.

### Via AWS CLI:

```bash
aws secretsmanager create-secret \
  --name admissions-agent/twilio \
  --description "Twilio WhatsApp API credentials for Admissions Agent" \
  --secret-string '{
    "account_sid":"ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "auth_token":"your-auth-token-here",
    "phone_number":"+14155238886"
  }' \
  --region us-west-2
```

**Replace**:
- `ACxxxxxxxx...` with your actual Account SID
- `your-auth-token-here` with your actual Auth Token
- `+14155238886` with your actual sandbox number

### Via AWS Console:

1. Go to **AWS Secrets Manager**: https://console.aws.amazon.com/secretsmanager/
2. Click **"Store a new secret"**
3. Select **"Other type of secret"**
4. Under **Key/value pairs**, add three entries:
   - Key: `account_sid`, Value: `ACxxxxxxxx...`
   - Key: `auth_token`, Value: `your-token-here`
   - Key: `phone_number`, Value: `+14155238886`
5. Click **"Next"**
6. **Secret name**: `admissions-agent/twilio`
7. **Description**: "Twilio WhatsApp API credentials"
8. Click **"Next"** (leave rotation settings as default)
9. Click **"Next"** (review)
10. Click **"Store"**

---

## Step 5: Deploy Updated Lambda Functions

The CDK stack has been updated to use Secrets Manager. Deploy the changes:

```bash
cd Backend/admissions-ai-agent
npx cdk deploy --require-approval never
```

This will:
- Update Form Submission Lambda to read Salesforce credentials from Secrets Manager
- Update WhatsApp Sender Lambda to read Twilio credentials from Secrets Manager
- Grant both Lambdas permission to access their respective secrets

---

## Step 6: Test WhatsApp Integration

### 6.1 Test Message Queuing

Test that messages are properly queued to SQS:

```bash
# Send a test message to the SQS queue
aws sqs send-message \
  --queue-url https://sqs.us-west-2.amazonaws.com/756493389182/twilio-whatsapp-queue \
  --message-body '{
    "phone_number": "+15551234567",
    "message": "Hello! This is a test message from Mapua Admissions.",
    "timing_preference": "as soon as possible",
    "student_name": "Test Student",
    "eum_msg_id": "test-msg-001",
    "queued_at": "'$(date -u +%Y-%m-%dT%H:%M:%S)'Z"
  }' \
  --region us-west-2
```

**Expected**: Message appears in SQS queue and gets processed by Lambda

### 6.2 Check Lambda Logs

```bash
# Check WhatsApp Sender Lambda logs
aws logs tail /aws/lambda/admissions-whatsapp-sender --follow --region us-west-2
```

**Expected Log Output**:
```
Successfully retrieved secret: admissions-agent/twilio
Processing WhatsApp message to +15551234567, ID: test-msg-001
WhatsApp sent successfully: SMxxxxxxxxxxxxxxxxxx
Logged message status to DynamoDB: test-msg-001
```

### 6.3 Check DynamoDB

```bash
# Verify message was logged to tracking table
aws dynamodb get-item \
  --table-name WhatsAppMessageTracking \
  --key '{"eum_msg_id": {"S": "test-msg-001"}}' \
  --region us-west-2
```

**Expected**: Record with status "queued" or "sent" and Twilio message SID

### 6.4 Check Your Phone

- You should receive the test WhatsApp message
- If you don't, check that:
  - Your phone number is verified in Twilio
  - You've joined the WhatsApp sandbox
  - The phone number format is E.164 (e.g., +15551234567)

---

## Step 7: Test Full Form Submission Flow

Test the complete end-to-end flow:

```bash
curl -X POST https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod/submit \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Maria",
    "lastName": "Santos",
    "email": "maria.santos@example.com",
    "cellPhone": "+15551234567",
    "headquarters": "Manila",
    "programType": "Graduate",
    "homePhone": "+15551234568"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Your inquiry has been submitted successfully. Please check your email for confirmation.",
  "leadId": "00Q5e00000XxxxxXXX"
}
```

**Verify in Salesforce**:
1. Go to Salesforce → **Leads** tab
2. Find "Maria Santos"
3. Verify custom fields are populated (Program Type, Headquarters)
4. Status should be "New"

---

## Troubleshooting

### "Unable to retrieve Twilio credentials from Secrets Manager"
- **Cause**: Lambda can't access the secret
- **Fix**:
  1. Verify secret name is exactly `admissions-agent/twilio`
  2. Check Lambda IAM role has `secretsmanager:GetSecretValue` permission
  3. Redeploy CDK stack

### "UNAUTHORIZED" Error from Twilio
- **Cause**: Wrong Account SID or Auth Token
- **Fix**:
  1. Verify credentials in Twilio Console
  2. Update the secret in Secrets Manager
  3. Clear Lambda cache (redeploy or update function)

### "Invalid 'To' Phone Number"
- **Cause**: Phone number not in E.164 format or not verified
- **Fix**:
  1. Ensure format is `+1XXXXXXXXXX` (country code + number)
  2. Verify the number in Twilio Console
  3. Join WhatsApp sandbox if testing personal number

### "Sandbox number not active"
- **Cause**: Haven't joined sandbox or sandbox expired
- **Fix**:
  1. Re-send join code from WhatsApp
  2. Verify you received confirmation message
  3. Sandbox expires after 3 days of inactivity - rejoin if needed

### Messages Not Being Delivered
- **Cause**: Multiple possible issues
- **Fix**:
  1. Check Lambda logs for errors
  2. Check SQS queue for failed messages (check DLQ)
  3. Verify Twilio account has credits (trial account has $15)
  4. Check Twilio Console → Monitor → Logs for delivery status

---

## Production Setup (Beyond Trial)

When you're ready to move to production:

1. **Upgrade Twilio Account**:
   - Add payment method
   - Upgrade from trial to paid account

2. **Request WhatsApp Business Profile**:
   - Go to: **Messaging** → **WhatsApp** → **Senders**
   - Click **"Request Approval"** for WhatsApp Business
   - Fill in business details
   - Wait for approval (typically 1-3 business days)

3. **Get Dedicated Phone Number**:
   - Purchase a WhatsApp-enabled phone number
   - Update secret in Secrets Manager with new number

4. **Remove Trial Restrictions**:
   - No need to verify recipient numbers
   - Increased message limits
   - No "Free Trial" prefix on messages

5. **Enable Message Templates**:
   - Create WhatsApp message templates for common use cases
   - Get templates approved by WhatsApp
   - Update agent to use templates for better deliverability

---

## Security Best Practices

⚠️ **Important**: Never commit credentials to Git!

1. **Rotate Credentials Regularly**:
   ```bash
   # Update secret in Secrets Manager
   aws secretsmanager update-secret \
     --secret-id admissions-agent/twilio \
     --secret-string '{
       "account_sid":"new-sid",
       "auth_token":"new-token",
       "phone_number":"+14155238886"
     }' \
     --region us-west-2
   ```

2. **Monitor Usage**:
   - Set up CloudWatch alarms for unusual SQS activity
   - Monitor Twilio usage in Console
   - Set budget alerts in Twilio

3. **Restrict Permissions**:
   - Lambda only has access to required secrets
   - Use least-privilege IAM policies
   - Review CloudTrail logs for Secrets Manager access

---

## Next Steps

After Twilio is working:
1. ✅ Test form submission creates Leads in Salesforce
2. ✅ Test WhatsApp messages are sent via Twilio
3. ⏭️ Deploy AgentCore with all credentials
4. ⏭️ Test full advisor handoff workflow end-to-end
5. ⏭️ Test chat interface with streaming responses

All credentials are now stored in AWS Secrets Manager for security.
