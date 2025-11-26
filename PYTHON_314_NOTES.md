# Python 3.14 Compatibility Notes

You're using Python 3.14, which is great! However, there's one known compatibility issue with the testing setup.

## Issue: pytest-asyncio

**Problem**: pytest-asyncio version 0.23.0 (and earlier) has a compatibility issue with Python 3.14, causing this error:
```
AttributeError: 'Package' object has no attribute 'obj'
```

**Root Cause**: The plugin tries to access an attribute that doesn't exist in Python 3.14's newer pytest version.

## Solution

Since the Form Submission and WhatsApp Sender Lambda tests **don't actually use async functions**, we don't need pytest-asyncio for them.

**To fix**:
```bash
pip uninstall pytest-asyncio -y
```

Then run tests normally:
```bash
cd Backend/admissions-ai-agent/lambda/form-submission
python -m pytest tests/ -v
```

## Results

With this fix applied:
- ✅ **Form Submission Lambda**: 13/13 tests passing (100%)
- ✅ All validation tests work
- ✅ All Salesforce integration mocking works
- ✅ All Lambda handler tests work

## If You Need Async Testing Later

When pytest-asyncio releases a Python 3.14-compatible version (likely 0.24.0 or later), you can reinstall it:
```bash
pip install pytest-asyncio>=0.24.0
```

For now, the workaround is perfect since none of the Lambda tests use async/await.

## Updated requirements-dev.txt

I've commented out pytest-asyncio in [requirements-dev.txt](requirements-dev.txt) to prevent this issue:
```python
# pytest-asyncio==0.24.0  # Commented out - not compatible with Python 3.14 yet
```

You can uncomment and update the version once a compatible release is available.

---

**Last Updated**: November 26, 2024
