# Lambda Layers

This directory contains Lambda Layers for shared Python dependencies across Lambda functions.

## Layers

### 1. Salesforce Layer
**Location:** `salesforce-layer/`
**Dependencies:** simple-salesforce, requests
**Size:** ~11 MB
**Used by:** Form Submission Lambda

Provides the `simple-salesforce` library for Salesforce CRM integration.

### 2. Twilio Layer
**Location:** `twilio-layer/`
**Dependencies:** twilio, PyJWT, requests, aiohttp
**Size:** ~3 MB
**Used by:** WhatsApp Sender Lambda

Provides the `twilio` library for WhatsApp messaging via Twilio API.

## Building Layers

Each layer has build scripts for different platforms:

### On Windows

```powershell
cd salesforce-layer
.\build.ps1

cd ../twilio-layer
.\build.ps1
```

### On Linux/macOS

```bash
cd salesforce-layer
chmod +x build.sh
./build.sh

cd ../twilio-layer
chmod +x build.sh
./build.sh
```

### Build Output

Each build creates:
- `python/` directory with installed dependencies
- `<layer-name>.zip` file ready for deployment

## Deployment

Layers are deployed via AWS CDK in the main infrastructure stack:

```typescript
// Salesforce Layer
const salesforceLayer = new lambda.LayerVersion(this, 'SalesforceLayer', {
  code: lambda.Code.fromAsset('layers/salesforce-layer/salesforce-layer.zip'),
  compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
  description: 'Salesforce simple-salesforce library'
});

// Twilio Layer
const twilioLayer = new lambda.LayerVersion(this, 'TwilioLayer', {
  code: lambda.Code.fromAsset('layers/twilio-layer/twilio-layer.zip'),
  compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
  description: 'Twilio API library for WhatsApp messaging'
});
```

Then attach to Lambda functions:

```typescript
const formSubmissionLambda = new lambda.Function(this, 'FormSubmissionFunction', {
  // ... other config
  layers: [salesforceLayer]
});

const whatsappSenderLambda = new lambda.Function(this, 'WhatsAppSenderFunction', {
  // ... other config
  layers: [twilioLayer]
});
```

## Layer Structure

AWS Lambda expects layers to follow this directory structure:

```
<layer-name>.zip
└── python/
    ├── <package-1>/
    ├── <package-2>/
    └── ...
```

When deployed, Lambda adds `/opt/python` to the Python path, making packages available via standard imports.

## Size Limits

- Maximum uncompressed layer size: 250 MB
- Maximum total function + layers size: 250 MB uncompressed
- Maximum 5 layers per function

Our layers:
- Salesforce: ~11 MB (well within limits)
- Twilio: ~3 MB (well within limits)

## Versioning

Layer versions are immutable once published. To update:
1. Modify `requirements.txt` in the layer directory
2. Rebuild the layer
3. Redeploy via CDK (creates new version)
4. Update Lambda functions to use new version

## Optimization

### Excluding Unnecessary Files

The build scripts automatically exclude:
- `__pycache__/` directories
- `.pyc` files (Python bytecode)
- `.dist-info` metadata (kept for compatibility)

### Alternative: Slim Builds

For further size reduction, consider:
- Using `pip install --no-deps` if transitive dependencies aren't needed
- Removing `.dist-info` directories after install
- Using compiled wheels for native dependencies

## Testing Layers Locally

Before deploying, test layers work with your Lambda code:

```bash
# Extract layer
unzip salesforce-layer.zip -d /tmp/layer

# Set PYTHONPATH
export PYTHONPATH=/tmp/layer/python:$PYTHONPATH

# Test import
python -c "import simple_salesforce; print('✓ Salesforce layer works')"
python -c "from twilio.rest import Client; print('✓ Twilio layer works')"
```

## Troubleshooting

### Windows Long Path Issues

If you encounter path length errors on Windows:
- Use the Python-based build approach (already implemented in build.ps1)
- Enable long paths in Windows (requires admin):
  ```powershell
  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
  ```

### Import Errors

If Lambda can't find packages from layer:
1. Verify layer structure has `python/` at root
2. Check Lambda runtime matches layer compatibility (Python 3.12)
3. Verify layer is attached to function in CDK
4. Check CloudWatch logs for detailed error messages

### Dependency Conflicts

If dependencies conflict between layers:
- Consolidate into single layer
- Pin specific versions in requirements.txt
- Use separate Lambda functions for conflicting dependencies

## CI/CD Integration

To automate layer builds in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Build Lambda Layers
  run: |
    cd Backend/admissions-ai-agent/layers/salesforce-layer
    ./build.sh
    cd ../twilio-layer
    ./build.sh

- name: Upload Layer Artifacts
  uses: actions/upload-artifact@v3
  with:
    name: lambda-layers
    path: |
      Backend/admissions-ai-agent/layers/**/*.zip
```

## Security

Layers inherit Lambda function's IAM role and VPC configuration. No additional security configuration needed for layers themselves.

Dependencies are from PyPI:
- **simple-salesforce**: Verified, actively maintained
- **twilio**: Official Twilio SDK
- **requests**: Industry standard HTTP library

Regularly update dependencies for security patches.
