# Deployment Dashboard Python Backend

Flask-based API backend for the Unified Release Dashboard.

## Local Development

```bash
# Install dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and settings

# Run locally
python app.py
```

API will be available at http://localhost:5000

## Endpoints

- `GET /` or `/api/deployments` - Get all deployments
- `GET /api/deployments/<service_name>` - Get deployments for a service
- `GET /api/deployments/<service_name>/<environment>` - Get specific deployment
- `GET /api/environments/<environment>` - Get all services in an environment
- `GET /api/stats` - Get deployment statistics
- `GET /health` - Health check

## Deploy to Lambda

This Flask app can also run as an AWS Lambda function. The Lambda handler is in `AWS/modules/shared-infrastructure/dashboard_lambda.py`.
