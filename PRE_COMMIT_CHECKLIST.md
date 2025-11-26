# Pre-Commit Checklist

Use this checklist before every `git commit` to ensure you're not committing sensitive data.

---

## 🔍 Quick Check (1 minute)

```bash
# See what you're about to commit
git status
git diff --cached

# Search for potential secrets
git diff --cached | grep -iE "(password|token|key|secret|api_key|credentials)"
```

---

## ✅ Checklist

### Files

- [ ] No `.env` files are staged (only `.env.example` should be committed)
- [ ] No `credentials.json` or similar files
- [ ] No `.agentcore/config.json` (contains AWS config)
- [ ] No `node_modules/` directories
- [ ] No `__pycache__/` directories
- [ ] No `.DS_Store` or system files
- [ ] No build artifacts (`*.zip`, `cdk.out/`, `.next/`, etc.)

### Code Review

- [ ] No hardcoded passwords or API keys
- [ ] No sensitive data in comments
- [ ] No `console.log()` or `print()` with sensitive data
- [ ] No commented-out code with credentials
- [ ] No TODO comments with sensitive information

### Configuration

- [ ] AWS Account IDs are parameterized (not hardcoded)
- [ ] Database connection strings use environment variables
- [ ] API endpoints are configurable
- [ ] Region settings are parameterized

### Lambda Functions

- [ ] Environment variables used for secrets (not hardcoded)
- [ ] No credentials in Lambda deployment packages
- [ ] Lambda layers don't contain secrets

---

## 🚨 Red Flags

Stop and review if you see any of these in `git diff`:

- `password =`
- `api_key =`
- `secret =`
- `token =`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- Email addresses (unless example.com)
- Phone numbers (unless +15551234567)
- Account IDs (unless documented examples)

---

## ⚙️ Automated Checks

### Install git-secrets (Recommended)

```bash
# macOS
brew install git-secrets

# Or install from source
git clone https://github.com/awslabs/git-secrets
cd git-secrets
make install

# Setup for your repo
cd /path/to/admissions-ai-agent
git secrets --install
git secrets --register-aws
```

This will prevent commits containing AWS credentials.

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Check for common secrets patterns
if git diff --cached | grep -iE "(password|token|key|secret|api_key|credentials)" | grep -v ".example"; then
    echo "⚠️  WARNING: Potential secrets detected!"
    echo "Review your changes with: git diff --cached"
    echo ""
    echo "If these are not secrets, you can bypass with: git commit --no-verify"
    exit 1
fi

# Check if .env files are staged
if git diff --cached --name-only | grep -E "\.env$|\.env\.local$|\.env\.production$"; then
    echo "❌ ERROR: .env files should not be committed!"
    echo "Found:"
    git diff --cached --name-only | grep -E "\.env$|\.env\.local$|\.env\.production$"
    echo ""
    echo "To unstage: git reset HEAD <file>"
    exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 🔄 If You Need to Commit Urgent Changes

If you're in a hurry but still want to be safe:

```bash
# Stage your changes
git add .

# Review ONLY the files you're committing
git diff --cached --name-only

# If you see any suspicious files
git reset HEAD <suspicious-file>

# Review the content
git diff --cached

# Commit when safe
git commit -m "Your message"
```

---

## 📝 Good Commit Messages

Instead of:
- ❌ "Update files"
- ❌ "Fix stuff"
- ❌ "WIP"

Use:
- ✅ "Add form validation to InquiryForm component"
- ✅ "Fix SSE streaming in Agent Proxy Lambda"
- ✅ "Update README with deployment instructions"

---

## 🆘 Emergency: I Committed Secrets!

If you realized you committed secrets:

### 1. DON'T PUSH YET!

If you haven't pushed to remote:
```bash
# Remove the last commit (keeps changes)
git reset HEAD~1

# Remove the secret from your files
# ... edit files ...

# Commit again without secrets
git add .
git commit -m "Your message"
```

### 2. IF YOU ALREADY PUSHED

**IMMEDIATELY**:
1. Revoke/change the exposed credentials
2. Contact your security team
3. Remove from Git history:

```bash
# For single file
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/file" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push --force --all

# Tell everyone to re-clone
```

4. **Still change the credentials** even after cleaning Git!

---

## 📚 Quick Reference

### Safe to Commit
- ✅ Source code (without secrets)
- ✅ `.env.example` files
- ✅ Documentation
- ✅ Configuration templates
- ✅ `.gitignore`
- ✅ Tests (without real data)

### Never Commit
- ❌ `.env` files with real values
- ❌ Credentials or passwords
- ❌ API keys or tokens
- ❌ Private keys (.pem, .key)
- ❌ `node_modules/`
- ❌ Build artifacts
- ❌ IDE settings (unless team-shared)
- ❌ OS files (.DS_Store, Thumbs.db)

---

## ✅ Final Check

Before pushing to remote:

```bash
# Review your commits
git log --oneline -5

# Review changes
git show

# Make sure .env files aren't in history
git log --all --full-history -- "*.env"

# Push when ready
git push
```

---

**Remember**: It takes 30 seconds to check, but hours to clean up a leaked secret!

Print this checklist or keep it handy while working with the codebase.
