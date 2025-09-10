# QuickBooks AI Agent - Deployment Guide

This guide will walk you through deploying the complete QuickBooks AI Agent system to AWS and GitHub Pages.

## Prerequisites

- AWS Account with appropriate permissions
- GitHub account
- Node.js 18+ installed
- Python 3.9+ installed
- AWS CLI configured
- Serverless Framework installed globally (`npm install -g serverless`)

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Pages  │───▶│   API Gateway    │───▶│  Lambda Function │
│   (Frontend)    │    │   + Lambda       │    │   (Backend)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  RAG Service    │    │   SageMaker     │
                       │   (Optional)    │    │   Endpoint      │
                       └─────────────────┘    └─────────────────┘
```

## Step 1: Prepare Your Repository

### 1.1 Clone and Initialize
```bash
git clone https://github.com/your-username/quickbooks-ai-agent.git
cd quickbooks-ai-agent
npm install
```

### 1.2 Generate API Keys
```bash
cd scripts
python generate_api_key.py
```

Save the generated API key and JWT secret - you'll need them for configuration.

## Step 2: Deploy SageMaker Model

### 2.1 Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### 2.2 Deploy the Model
```bash
cd sagemaker
pip install -r requirements.txt
python model_deployment.py --action deploy --model-id microsoft/DialoGPT-medium
```

This will create a SageMaker endpoint. Note the endpoint name for later configuration.

**Expected Output:**
```json
{
  "endpoint_name": "quickbooks-ai-20240909-182000",
  "endpoint_arn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/quickbooks-ai-20240909-182000",
  "status": "InService"
}
```

## Step 3: Set Up RAG Service (Optional)

### 3.1 Deploy RAG Service to EC2 or Container
```bash
cd rag
pip install -r requirements.txt
python knowledge_base.py  # Initialize knowledge base
python rag_service.py     # Start service (for testing)
```

For production, deploy this to:
- AWS ECS/Fargate
- EC2 instance
- AWS Lambda (for smaller models)

### 3.2 RAG Service Docker Deployment
```bash
# Create Dockerfile in rag/ directory
cat > rag/Dockerfile << EOF
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "rag_service.py"]
EOF

# Build and deploy
docker build -t quickbooks-rag rag/
docker run -p 5000:5000 quickbooks-rag
```

## Step 4: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

### Required Secrets:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `API_KEY`: Generated API key from Step 1.2
- `JWT_SECRET`: Generated JWT secret from Step 1.2

### Required Variables:
- `AWS_REGION`: AWS region (e.g., us-east-1)
- `SAGEMAKER_ENDPOINT_NAME`: Endpoint name from Step 2.2
- `RAG_SERVICE_URL`: URL of RAG service (if deployed)
- `CORS_ORIGIN`: Frontend domain (e.g., https://username.github.io)

## Step 5: Deploy Backend to AWS Lambda

### 5.1 Configure Serverless
```bash
cd backend
npm init -y
npm install serverless-python-requirements
```

### 5.2 Set Environment Variables
Create `.env` file in backend/:
```bash
SAGEMAKER_ENDPOINT_NAME=your-endpoint-name
RAG_SERVICE_URL=http://your-rag-service-url:5000
API_KEY=your-generated-api-key
JWT_SECRET=your-generated-jwt-secret
CORS_ORIGIN=https://username.github.io/quickbooks-ai-agent
```

### 5.3 Deploy
```bash
serverless deploy --stage prod
```

**Expected Output:**
```
endpoints:
  ANY - https://abc123def4.execute-api.us-east-1.amazonaws.com/prod/{proxy+}
  ANY - https://abc123def4.execute-api.us-east-1.amazonaws.com/prod/
```

Save the API Gateway URL for frontend configuration.

## Step 6: Deploy Frontend to GitHub Pages

### 6.1 Update Frontend Configuration
Edit `frontend/app.js` and update the API endpoint:
```javascript
this.apiEndpoint = 'https://your-api-gateway-url.amazonaws.com/prod';
```

### 6.2 Enable GitHub Pages
1. Go to repository Settings > Pages
2. Select "Deploy from a branch"
3. Choose "main" branch and "/frontend" folder
4. Save

### 6.3 Automatic Deployment
Push to main branch to trigger automatic deployment:
```bash
git add .
git commit -m "Deploy QuickBooks AI Agent"
git push origin main
```

## Step 7: Configure Custom Domain (Optional)

### 7.1 Add CNAME Record
Create `frontend/CNAME` file:
```
your-domain.com
```

### 7.2 Update DNS
Add CNAME record pointing to `username.github.io`

## Step 8: Testing Deployment

### 8.1 Test Backend API
```bash
curl -X GET https://your-api-gateway-url.amazonaws.com/prod/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "sagemaker": "configured",
    "rag": "configured"
  }
}
```

### 8.2 Test Frontend
1. Visit your GitHub Pages URL
2. Try the quick action buttons
3. Send a test message
4. Verify API connectivity in browser console

### 8.3 Test RAG Functionality
```bash
curl -X POST https://your-api-gateway-url.amazonaws.com/prod/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"query": "bank connection"}'
```

## Monitoring and Maintenance

### CloudWatch Logs
- Lambda logs: `/aws/lambda/quickbooks-ai-agent-prod-api`
- SageMaker logs: Check SageMaker console

### Cost Optimization
- Use SageMaker Serverless Inference for lower traffic
- Implement auto-scaling for RAG service
- Monitor CloudWatch metrics for usage patterns

### Updating the System

#### Update Knowledge Base:
```bash
cd rag
python -c "
from knowledge_base import QuickBooksRAG, Document
rag = QuickBooksRAG()
# Add new documents
new_docs = [Document(...)]  # Your new documents
rag.add_documents(new_docs)
"
```

#### Update Model:
```bash
cd sagemaker
python model_deployment.py --action delete --endpoint-name old-endpoint
python model_deployment.py --action deploy --model-id new-model-id
```

#### Update Frontend:
- Push changes to main branch
- GitHub Actions will automatically deploy

## Troubleshooting

### Common Issues:

1. **SageMaker Endpoint Not Ready**
   - Check SageMaker console for endpoint status
   - Verify IAM permissions
   - Check CloudWatch logs

2. **CORS Issues**
   - Verify CORS_ORIGIN environment variable
   - Check API Gateway CORS configuration

3. **RAG Service Connection Failed**
   - Verify RAG service is running
   - Check network connectivity
   - Validate RAG_SERVICE_URL

4. **Authentication Errors**
   - Verify API_KEY matches between frontend and backend
   - Check JWT_SECRET configuration
   - Validate request headers

### Support Resources:
- AWS SageMaker Documentation
- Serverless Framework Docs
- GitHub Pages Documentation
- Project README.md

## Security Considerations

- API keys should be rotated regularly
- Use HTTPS for all communications
- Monitor CloudWatch for unusual activity
- Implement proper IAM policies with least privilege
- Keep dependencies updated

## Cost Estimation

**Monthly costs (approximate):**
- SageMaker Endpoint: $100-500 (depending on instance type)
- Lambda: $5-20 (for typical usage)
- API Gateway: $3-10 (per million requests)
- S3/CloudWatch: $1-5
- **Total**: $109-535/month

Use SageMaker Serverless Inference to reduce costs for low-traffic applications.
