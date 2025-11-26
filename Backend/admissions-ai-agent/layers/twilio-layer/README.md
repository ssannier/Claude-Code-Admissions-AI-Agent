# Twilio Lambda Layer

This Lambda Layer provides the `twilio` library for Python Lambda functions.

## Contents

- `twilio==9.0.4`: Python client library for Twilio API
- `PyJWT==2.8.0`: JSON Web Token library (dependency of twilio)
- `requests==2.31.0`: HTTP library (dependency of twilio)

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

This will create `twilio-layer.zip` containing the layer contents.

## Usage

This layer is used by:
- **WhatsApp Sender Lambda**: Sends WhatsApp messages via Twilio API

## Directory Structure

The layer follows AWS Lambda's required structure:

```
python/
├── twilio/
├── jwt/
├── requests/
└── [other dependencies]
```

When deployed, Lambda automatically adds `/opt/python` to the Python path, making these packages available via `from twilio.rest import Client`.

## Deployment

The layer is deployed via AWS CDK as part of the main infrastructure stack:

```typescript
const twilioLayer = new lambda.LayerVersion(this, 'TwilioLayer', {
  code: lambda.Code.fromAsset('layers/twilio-layer/twilio-layer.zip'),
  compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
  description: 'Twilio API library for WhatsApp messaging'
});
```

## Size Optimization

The built layer is approximately 5-7 MB, well under Lambda's 50 MB zipped layer limit.

## Version Management

- twilio 9.0.4: Latest stable version with WhatsApp support
- PyJWT 2.8.0: Latest stable version with security updates
- requests 2.31.0: Stable version with security updates

To update versions, modify `requirements.txt` and rebuild.

## WhatsApp Configuration

This layer enables the WhatsApp Sender Lambda to:
1. Send WhatsApp messages via Twilio's WhatsApp Business API
2. Authenticate with Twilio credentials
3. Track message delivery status

The Twilio client is initialized in the Lambda handler:

```python
from twilio.rest import Client

client = Client(
    os.environ['TWILIO_ACCOUNT_SID'],
    os.environ['TWILIO_AUTH_TOKEN']
)

message = client.messages.create(
    from_='whatsapp:+15559876543',
    to='whatsapp:+15551234567',
    body='Your message here'
)
```
