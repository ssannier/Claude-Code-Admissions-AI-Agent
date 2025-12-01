# Salesforce Setup Guide for Admissions Agent

## Step 1: Get Your Security Token

1. **Log into Salesforce**: https://login.salesforce.com
   - Use the credentials you just created

2. **Access Settings**:
   - Click your profile icon (top-right corner)
   - Select **"Settings"**

3. **Reset Security Token**:
   - In the left sidebar, go to: **Personal** → **Reset My Security Token**
   - Click **"Reset Security Token"** button
   - Check your email - Salesforce will send you the security token

4. **Save Your Credentials**:
   ```
   Username: [your-email@example.com]
   Password: [your-password]
   Security Token: [from email - looks like: AbCdEfGhIjKlMnOpQrSt]
   ```

---

## Step 2: Create Custom Fields on Lead Object

The application needs three custom fields to track student preferences.

### 2.1 Navigate to Lead Object Manager

1. Click the **gear icon** (⚙️) in top-right → **Setup**
2. In the Quick Find box (left sidebar), type: **"Object Manager"**
3. Click **"Object Manager"**
4. Find and click **"Lead"** in the list

### 2.2 Create "Program Type" Field

1. Click **"Fields & Relationships"** tab
2. Click **"New"** button (top-right)
3. Select field type: **"Picklist"**
4. Click **"Next"**
5. Fill in the details:
   - **Field Label**: `Program Type`
   - **Field Name**: `Program_Type` (auto-fills as `Program_Type__c`)
   - **Values**: Enter these options (one per line):
     ```
     Undergraduate
     Graduate
     Certificate
     Continuing Education
     ```
   - Check **"Use first value as default value"**
6. Click **"Next"**
7. **Field-Level Security**: Check **"Visible"** for all profiles
8. Click **"Next"**
9. **Page Layouts**: Check all (to show field on all Lead layouts)
10. Click **"Save"**

### 2.3 Create "Headquarters" Field

1. Click **"New"** button again
2. Select field type: **"Picklist"**
3. Click **"Next"**
4. Fill in the details:
   - **Field Label**: `Headquarters`
   - **Field Name**: `Headquarters` (auto-fills as `Headquarters__c`)
   - **Values**: Enter these options (one per line):
     ```
     Manila
     Makati
     Cebu
     Davao
     Online
     ```
   - Check **"Use first value as default value"**
5. Click **"Next"**
6. **Field-Level Security**: Check **"Visible"** for all profiles
7. Click **"Next"**
8. **Page Layouts**: Check all
9. Click **"Save"**

### 2.4 Create "Timing Preference" Field

1. Click **"New"** button again
2. Select field type: **"Picklist"**
3. Click **"Next"**
4. Fill in the details:
   - **Field Label**: `Timing Preference`
   - **Field Name**: `Timing_Preference` (auto-fills as `Timing_Preference__c`)
   - **Values**: Enter these options (one per line):
     ```
     as soon as possible
     2 hours
     4 hours
     tomorrow morning
     ```
   - Check **"Use first value as default value"**
5. Click **"Next"**
6. **Field-Level Security**: Check **"Visible"** for all profiles
7. Click **"Next"**
8. **Page Layouts**: Check all
9. Click **"Save"**

---

## Step 3: Verify Custom Fields

1. Go back to **Object Manager** → **Lead** → **Fields & Relationships**
2. You should see these three new custom fields:
   - `Program_Type__c` (Picklist)
   - `Headquarters__c` (Picklist)
   - `Timing_Preference__c` (Picklist)

---

## Step 4: Configure Lambda Environment Variables

Now we'll add your Salesforce credentials to the AWS Lambda functions.

### Via AWS Console:

1. **Navigate to Lambda Functions**:
   - AWS Console → Lambda → Functions

2. **Update Form Submission Lambda**:
   - Select function: `admissions-form-submission`
   - Go to **Configuration** tab → **Environment variables** → **Edit**
   - Add these variables:
     ```
     SF_USERNAME = your-salesforce-email@example.com
     SF_PASSWORD = your-salesforce-password
     SF_TOKEN = your-security-token-from-email
     ```
   - Click **Save**

3. **Update WhatsApp Sender Lambda** (if using Salesforce features):
   - Select function: `admissions-whatsapp-sender`
   - Same steps as above (may not need Salesforce creds depending on workflow)

### Via AWS CLI:

```bash
# Form Submission Lambda
aws lambda update-function-configuration \
  --function-name admissions-form-submission \
  --environment "Variables={
    SF_USERNAME=your-email@example.com,
    SF_PASSWORD=your-password,
    SF_TOKEN=your-security-token,
    LOG_LEVEL=INFO
  }" \
  --region us-west-2

# Verify it worked
aws lambda get-function-configuration \
  --function-name admissions-form-submission \
  --region us-west-2 \
  --query "Environment.Variables"
```

---

## Step 5: Test Salesforce Integration

### 5.1 Test Form Submission

```bash
curl -X POST https://9ppnenaq01.execute-api.us-west-2.amazonaws.com/prod/submit \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Test",
    "lastName": "Student",
    "email": "test@example.com",
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
  "leadId": "00Q..."
}
```

### 5.2 Verify in Salesforce

1. Go to Salesforce → **App Launcher** (grid icon, top-left)
2. Search for and open **"Sales"** app
3. Click **"Leads"** tab
4. You should see your test lead: "Test Student"
5. Click on it to view details - verify custom fields are populated

---

## Step 6: Test Salesforce Queries (Optional)

You can test the Salesforce query functionality directly:

```python
# Test script (run locally with Python)
from simple_salesforce import Salesforce

sf = Salesforce(
    username='your-email@example.com',
    password='your-password',
    security_token='your-security-token'
)

# Query Leads
results = sf.query("""
    SELECT Id, FirstName, LastName, Email, Phone, Status,
           Program_Type__c, Headquarters__c, Timing_Preference__c
    FROM Lead
    WHERE Email = 'test@example.com'
    LIMIT 1
""")

print(f"Found {results['totalSize']} lead(s)")
for record in results['records']:
    print(f"Name: {record['FirstName']} {record['LastName']}")
    print(f"Status: {record['Status']}")
    print(f"Program: {record['Program_Type__c']} at {record['Headquarters__c']}")
```

---

## Troubleshooting

### "INVALID_LOGIN" Error
- **Cause**: Wrong username, password, or security token
- **Fix**:
  1. Verify credentials are correct
  2. Reset security token if password was changed
  3. Check for extra spaces in environment variables

### "MALFORMED_ID" or "INVALID_FIELD" Error
- **Cause**: Custom fields not created correctly
- **Fix**:
  1. Verify field API names end with `__c`
  2. Check fields are visible to your user profile
  3. Ensure picklist values match exactly

### "INVALID_SESSION_ID" Error
- **Cause**: Security token expired or wrong
- **Fix**: Reset security token and update Lambda environment variables

### Custom Fields Not Showing
- **Cause**: Fields not added to page layout
- **Fix**:
  1. Object Manager → Lead → Page Layouts
  2. Edit "Lead Layout"
  3. Drag custom fields from top palette to the layout
  4. Save

---

## Security Best Practices

⚠️ **Important**: Never commit credentials to Git!

### For Production:
1. Use **AWS Secrets Manager** instead of environment variables:
   ```bash
   # Store credentials in Secrets Manager
   aws secretsmanager create-secret \
     --name admissions-agent/salesforce \
     --secret-string '{
       "username":"your-email@example.com",
       "password":"your-password",
       "token":"your-security-token"
     }' \
     --region us-west-2
   ```

2. Update Lambda to read from Secrets Manager (code modification needed)

### For Development:
- Keep credentials in `.env.local` (already in .gitignore)
- Never share screenshots with credentials visible
- Rotate security token regularly

---

## Next Steps

After Salesforce is working:
1. ✅ Test form submission creates Leads
2. ✅ Verify custom fields are populated
3. ⏭️ Set up Twilio/WhatsApp integration
4. ⏭️ Test full advisor handoff workflow
5. ⏭️ Deploy AgentCore with Salesforce credentials

All credentials should be added to [DEPLOYMENT_CONFIG.md](c:\Users\seans\CIC\Claude Code Tests\Claude-Code-Admissions-AI-Agent\DEPLOYMENT_CONFIG.md) for reference (mark as `<from-secrets>`).
