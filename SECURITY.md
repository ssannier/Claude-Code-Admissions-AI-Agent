# Security Guidelines

## ⚠️ IMPORTANT: Never Commit Secrets to Git!

This document outlines security best practices for the AI Admissions Agent project.

---

## 🔒 Secrets Management

### What Should NEVER Be Committed

❌ **NEVER commit these files**:
- `.env`
- `.env.local`
- `.env.production`
- Any file containing credentials
- `credentials.json`
- `.agentcore/config.json` (contains sensitive config)
- SSH keys (`.pem`, `.key` files)
- API tokens or passwords

### What SHOULD Be Committed

✅ **These template files are safe to commit**:
- `.env.example` (template with placeholder values)
- `.gitignore` (already configured)
- Documentation
- Source code (without hardcoded credentials)

---

## 🛡️ Setting Up Secrets

### 1. Environment Variables (Local Development)

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual credentials
# The .gitignore will prevent this from being committed
```

### 2. AWS Secrets Manager (Production)

Store sensitive values in AWS Secrets Manager:

```bash
# Store GitHub token
aws secretsmanager create-secret \
  --name github-token \
  --secret-string "your-github-personal-access-token"

# Store Salesforce credentials
aws secretsmanager create-secret \
  --name admissions-agent/salesforce \
  --secret-string '{
    "username": "your-username@example.com",
    "password": "your-password",
    "security_token": "your-token",
    "domain": "test"
  }'

# Store Twilio credentials
aws secretsmanager create-secret \
  --name admissions-agent/twilio \
  --secret-string '{
    "account_sid": "ACxxxxx",
    "auth_token": "your-token",
    "whatsapp_from": "whatsapp:+14155238886"
  }'
```

### 3. Lambda Environment Variables

Set via CDK or AWS Console (never hardcode in code):

```typescript
// In CDK stack
environment: {
  SALESFORCE_USERNAME: secretsmanager.Secret.fromSecretNameV2(
    this, 'SalesforceSecret', 'admissions-agent/salesforce'
  ).secretValueFromJson('username').toString(),
  // ... other variables
}
```

---

## 🔍 Checking for Leaked Secrets

### Before Committing

```bash
# Check what you're about to commit
git status
git diff

# Search for potential secrets in staged files
git diff --cached | grep -E "(password|token|key|secret|api_key)"

# Use git-secrets tool (recommended)
git secrets --scan
```

### After Committing (If You Made a Mistake)

If you accidentally committed secrets:

1. **Immediately revoke the credentials** (change passwords, regenerate tokens)
2. Remove from Git history:

```bash
# For recent commit
git reset HEAD~1
git commit -m "Remove sensitive data"

# For older commits (use BFG Repo Cleaner)
# https://rtyley.github.io/bfg-repo-cleaner/
```

3. Force push (if already pushed to remote):
```bash
git push --force
```

4. **Still revoke the credentials** even after removing from Git!

---

## 📋 Security Checklist

### Before Initial Commit

- [ ] `.gitignore` is in place
- [ ] `.env.example` created (without real values)
- [ ] No hardcoded credentials in source code
- [ ] No API keys in configuration files
- [ ] Reviewed all files to be committed

### Before Each Commit

- [ ] Run `git diff` to review changes
- [ ] Search for "password", "token", "key" in diff
- [ ] Verify `.env` files are not staged
- [ ] No console.log() with sensitive data

### Before Deployment

- [ ] All secrets stored in AWS Secrets Manager or Parameter Store
- [ ] Lambda functions use environment variables (not hardcoded)
- [ ] IAM roles follow least-privilege principle
- [ ] API endpoints have proper authentication
- [ ] CORS configured appropriately (not "*" in production)

---

## 🔐 Credential Rotation

### Regular Rotation Schedule

- **Salesforce**: Every 90 days
- **Twilio**: Every 90 days
- **AWS Access Keys**: Every 90 days
- **GitHub Tokens**: Every 90 days
- **Database Passwords**: Every 90 days

### How to Rotate

1. Generate new credentials in the service
2. Update AWS Secrets Manager
3. Restart Lambda functions or redeploy
4. Verify new credentials work
5. Revoke old credentials

```bash
# Update secret in AWS
aws secretsmanager update-secret \
  --secret-id admissions-agent/salesforce \
  --secret-string '{"username":"...","password":"..."}'

# Force Lambda to use new values
aws lambda update-function-configuration \
  --function-name YourFunction \
  --environment "Variables={FORCE_REFRESH=$(date +%s)}"
```

---

## 🚨 Incident Response

### If Secrets Are Exposed

1. **Immediate Actions** (within minutes):
   - Revoke exposed credentials
   - Change all passwords
   - Regenerate all API tokens
   - Disable affected API keys

2. **Short Term** (within hours):
   - Review access logs for unauthorized use
   - Remove secrets from Git history
   - Update all deployment configurations
   - Notify security team

3. **Long Term** (within days):
   - Post-mortem analysis
   - Update security procedures
   - Consider implementing additional safeguards
   - Document the incident

### Contact Information

- **AWS Security**: https://aws.amazon.com/security/vulnerability-reporting/
- **Salesforce Security**: trust.salesforce.com
- **Twilio Security**: https://www.twilio.com/security

---

## 🛠️ Security Tools

### Recommended Tools

1. **git-secrets**: Prevents committing secrets
   ```bash
   brew install git-secrets  # macOS
   git secrets --install
   git secrets --register-aws
   ```

2. **truffleHog**: Finds secrets in Git history
   ```bash
   pip install truffleHog
   truffleHog --regex --entropy=False .
   ```

3. **detect-secrets**: Pre-commit hook
   ```bash
   pip install detect-secrets
   detect-secrets scan > .secrets.baseline
   ```

4. **AWS IAM Access Analyzer**: Reviews IAM policies
   - Enable in AWS Console
   - Review findings regularly

---

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Salesforce Security Guide](https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/)

---

## ✅ Security Verification

Before going to production, verify:

- [ ] No credentials in Git history
- [ ] All secrets in AWS Secrets Manager
- [ ] IAM roles use least privilege
- [ ] Lambda functions have proper VPC configuration
- [ ] API Gateway has authentication
- [ ] CloudWatch logs don't contain sensitive data
- [ ] S3 buckets have proper access controls
- [ ] Database encryption at rest enabled
- [ ] SSL/TLS for all communications
- [ ] Regular security audits scheduled

---

**Remember**: Security is everyone's responsibility. When in doubt, ask!

**Last Updated**: November 25, 2024
