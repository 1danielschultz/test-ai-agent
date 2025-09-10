# QuickBooks AI Agent - Development Guide

## Development Environment Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Git
- VS Code (recommended)

### Local Setup
```bash
# Clone repository
git clone https://github.com/your-username/quickbooks-ai-agent.git
cd quickbooks-ai-agent

# Install dependencies
npm install
pip install -r rag/requirements.txt
pip install -r backend/requirements.txt
pip install -r sagemaker/requirements.txt
```

## Project Structure

```
quickbooks-ai-agent/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD
├── frontend/               # GitHub Pages web app
│   ├── index.html         # Main HTML file
│   ├── app.js            # Frontend JavaScript
│   └── styles.css        # CSS styles
├── backend/               # AWS Lambda API
│   ├── lambda_handler.py # Main Lambda function
│   ├── auth.py          # Authentication utilities
│   ├── serverless.yml   # Serverless config
│   └── requirements.txt # Python dependencies
├── rag/                  # RAG knowledge base
│   ├── knowledge_base.py # RAG implementation
│   ├── rag_service.py   # REST API service
│   └── requirements.txt # Python dependencies
├── sagemaker/           # AWS SageMaker
│   ├── model_deployment.py # Model deployment
│   ├── inference.py     # Custom inference code
│   └── requirements.txt # Python dependencies
├── scripts/             # Utility scripts
│   └── generate_api_key.py # API key generator
└── docs/               # Documentation
```

## Local Development

### Running Frontend Locally
```bash
cd frontend
python -m http.server 8000
# Visit http://localhost:8000
```

### Running RAG Service Locally
```bash
cd rag
python rag_service.py
# Service runs on http://localhost:5000
```

### Testing Backend Locally
```bash
cd backend
python lambda_handler.py
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... code changes ...

# Test locally
npm test
python -m pytest

# Commit and push
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

### 2. Code Quality
```bash
# Python linting
flake8 backend/ rag/ sagemaker/
black backend/ rag/ sagemaker/

# JavaScript linting
npx eslint frontend/app.js

# Security scanning
bandit -r backend/ rag/ sagemaker/
```

### 3. Testing
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Frontend tests
npm test
```

## Configuration

### Environment Variables
Create `.env` files for local development:

**backend/.env**:
```
SAGEMAKER_ENDPOINT_NAME=quickbooks-ai-dev
RAG_SERVICE_URL=http://localhost:5000
API_KEY=dev-api-key-123
JWT_SECRET=dev-jwt-secret-456
CORS_ORIGIN=http://localhost:8000
```

**rag/.env**:
```
MODEL_NAME=all-MiniLM-L6-v2
INDEX_PATH=./vector_store
PORT=5000
```

### VS Code Configuration
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/vector_store": true
  }
}
```

## Debugging

### Frontend Debugging
- Use browser DevTools
- Check Console for JavaScript errors
- Monitor Network tab for API calls
- Use browser debugger breakpoints

### Backend Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Local Lambda testing
sam local start-api
```

### RAG Service Debugging
```bash
# Enable verbose logging
python rag_service.py --debug

# Test knowledge base
python -c "
from knowledge_base import QuickBooksRAG
rag = QuickBooksRAG()
results = rag.search('test query')
print(results)
"
```

## Adding New Features

### Adding New Knowledge Base Documents
```python
# rag/knowledge_base.py

def create_quickbooks_knowledge_base():
    documents = [
        # ... existing documents ...
        Document(
            id="qb_new_001",
            title="New Feature Documentation",
            content="Detailed content about the new feature...",
            category="New Category",
            keywords=["new", "feature", "keywords"],
            source_url="https://quickbooks.intuit.com/new-feature"
        )
    ]
    return documents
```

### Adding New API Endpoints
```python
# backend/lambda_handler.py

def handle_new_endpoint(self, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle new endpoint requests"""
    try:
        # Implementation here
        return self.create_response(200, {"result": "success"})
    except Exception as e:
        logger.error(f"Error in new endpoint: {e}")
        return self.create_response(500, {"error": "Internal server error"})

# Add to lambda_handler function
elif path == '/new-endpoint' and method == 'POST':
    return handler.handle_new_endpoint(event)
```

### Adding Frontend Components
```javascript
// frontend/app.js

class NewComponent {
    constructor(container) {
        this.container = container;
        this.render();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="new-component">
                <!-- Component HTML -->
            </div>
        `;
        this.bindEvents();
    }
    
    bindEvents() {
        // Event listeners
    }
}
```

## Performance Optimization

### Frontend Optimization
- Minimize JavaScript bundle size
- Optimize images and assets
- Use browser caching
- Implement lazy loading

### Backend Optimization
- Optimize Lambda cold starts
- Use connection pooling
- Implement caching
- Monitor CloudWatch metrics

### RAG Optimization
- Use smaller embedding models for faster inference
- Implement result caching
- Optimize vector search parameters
- Consider GPU acceleration

## Testing Strategy

### Unit Tests
```python
# tests/test_knowledge_base.py
import pytest
from rag.knowledge_base import QuickBooksRAG

def test_document_search():
    rag = QuickBooksRAG()
    results = rag.search("test query")
    assert len(results) >= 0
```

### Integration Tests
```python
# tests/integration/test_api.py
import requests

def test_chat_endpoint():
    response = requests.post(
        "http://localhost:3000/chat",
        json={"message": "test message"},
        headers={"Authorization": "Bearer test-key"}
    )
    assert response.status_code == 200
```

### Frontend Tests
```javascript
// tests/frontend.test.js
describe('QuickBooks AI', () => {
    test('should initialize correctly', () => {
        const ai = new QuickBooksAI();
        expect(ai).toBeDefined();
    });
});
```

## Deployment Pipeline

### Development Environment
- Automatic deployment on push to `develop` branch
- Uses development AWS resources
- Includes debugging features

### Staging Environment
- Deployed from `staging` branch
- Production-like environment
- Used for final testing

### Production Environment
- Deployed from `main` branch
- Full security and monitoring
- Automated rollback on failures

## Monitoring and Logging

### Application Metrics
- API response times
- Error rates
- User interactions
- RAG search performance

### Infrastructure Metrics
- Lambda execution duration
- SageMaker endpoint latency
- Memory and CPU usage
- Cost tracking

### Logging Best Practices
```python
import logging

logger = logging.getLogger(__name__)

def example_function():
    logger.info("Starting function execution")
    try:
        # Function logic
        logger.debug("Debug information")
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check CORS_ORIGIN environment variable
   - Verify frontend domain matches CORS settings

2. **Authentication Failures**
   - Verify API key configuration
   - Check JWT secret consistency

3. **RAG Search Issues**
   - Verify knowledge base initialization
   - Check embedding model availability

4. **SageMaker Connection Issues**
   - Verify endpoint is InService
   - Check IAM permissions

### Debug Commands
```bash
# Check API connectivity
curl -X GET https://your-api-url.com/health

# Test RAG service
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Validate frontend
python -m http.server 8000 --directory frontend
```

## Contributing Guidelines

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Use meaningful commit messages
5. Create pull requests for review

## Security Considerations

- Never commit API keys or secrets
- Use environment variables for configuration
- Implement input validation
- Follow OWASP security guidelines
- Regular dependency updates
