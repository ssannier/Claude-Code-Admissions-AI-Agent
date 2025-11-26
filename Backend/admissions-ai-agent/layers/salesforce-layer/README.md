# Salesforce Lambda Layer

This Lambda Layer provides the `simple-salesforce` library for Python Lambda functions.

## Contents

- `simple-salesforce==1.12.6`: Python client library for Salesforce REST API
- `requests==2.31.0`: HTTP library (dependency of simple-salesforce)

## Building the Layer

### On Linux/macOS

```bash
chmod +x build.sh
./build.sh
```

### On Windows

```powershell
.\build.ps1
```

This will create `salesforce-layer.zip` containing the layer contents.

## Usage

This layer is used by:
- **Form Submission Lambda**: Creates Salesforce Leads from web form submissions

## Directory Structure

The layer follows AWS Lambda's required structure:

```
python/
├── simple_salesforce/
├── requests/
└── [other dependencies]
```

When deployed, Lambda automatically adds `/opt/python` to the Python path, making these packages available via `import simple_salesforce`.

## Deployment

The layer is deployed via AWS CDK as part of the main infrastructure stack:

```typescript
const salesforceLayer = new lambda.LayerVersion(this, 'SalesforceLayer', {
  code: lambda.Code.fromAsset('layers/salesforce-layer/salesforce-layer.zip'),
  compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
  description: 'Salesforce simple-salesforce library'
});
```

## Size Optimization

The built layer is approximately 2-3 MB, well under Lambda's 50 MB zipped layer limit.

## Version Management

- simple-salesforce 1.12.6: Latest stable version with OAuth and session management
- requests 2.31.0: Stable version with security updates

To update versions, modify `requirements.txt` and rebuild.
