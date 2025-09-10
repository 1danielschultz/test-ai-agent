# QuickBooks AI Agent - API Documentation

## Base URL
```
https://your-api-gateway-url.amazonaws.com/prod
```

## Authentication

All API endpoints require authentication using Bearer tokens in the Authorization header:

```http
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

- **Default Limit**: 100 requests per hour per user
- **Rate Limit Headers**: Check `Retry-After` header when receiving 429 status
- **Rate Limit Reset**: Rolling window of 1 hour

## Endpoints

### Health Check
Check the API service status.

**Endpoint**: `GET /health`

**Headers**: None required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-09-09T18:27:58Z",
  "version": "1.0.0",
  "services": {
    "sagemaker": "configured",
    "rag": "configured"
  }
}
```

### Chat with AI
Send a message to the QuickBooks AI assistant.

**Endpoint**: `POST /chat`

**Headers**:
- `Content-Type: application/json`
- `Authorization: Bearer YOUR_API_KEY`

**Request Body**:
```json
{
  "message": "How do I connect my bank account to QuickBooks?",
  "use_rag": true,
  "max_length": 300,
  "temperature": 0.7
}
```

**Parameters**:
- `message` (string, required): User's question or message
- `use_rag` (boolean, optional): Whether to use RAG context (default: true)
- `max_length` (integer, optional): Maximum response length (default: 300)
- `temperature` (float, optional): Response creativity (0.0-1.0, default: 0.7)

**Response**:
```json
{
  "response": "To connect your bank account to QuickBooks Online, follow these steps...",
  "context_used": true,
  "context_length": 1250,
  "model_info": {
    "model_id": "microsoft/DialoGPT-medium",
    "temperature": 0.7,
    "max_length": 300
  },
  "timestamp": "2024-09-09T18:27:58Z",
  "request_id": "abc123-def456-ghi789"
}
```

### Search Knowledge Base
Search the RAG knowledge base for relevant documents.

**Endpoint**: `POST /search`

**Headers**:
- `Content-Type: application/json`
- `Authorization: Bearer YOUR_API_KEY`

**Request Body**:
```json
{
  "query": "bank connection issues",
  "top_k": 5,
  "min_score": 0.5
}
```

**Parameters**:
- `query` (string, required): Search query
- `top_k` (integer, optional): Number of results to return (default: 5)
- `min_score` (float, optional): Minimum relevance score (default: 0.5)

**Response**:
```json
{
  "query": "bank connection issues",
  "results": [
    {
      "id": "qb001",
      "title": "Connecting Bank Accounts to QuickBooks Online",
      "content": "To connect your bank account to QuickBooks Online...",
      "category": "Banking",
      "keywords": ["bank connection", "banking", "connect account"],
      "score": 0.85,
      "relevance": "high",
      "source_url": "https://quickbooks.intuit.com/learn-support/..."
    }
  ],
  "total_results": 3
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Message is required",
  "message": "The request body must include a non-empty message field"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Valid API key required"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests"
}
```
**Headers**: `Retry-After: 3600`

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

### 503 Service Unavailable
```json
{
  "error": "RAG service not configured",
  "message": "RAG search functionality is not available"
}
```

## CORS

The API supports CORS with the following headers:
- `Access-Control-Allow-Origin`: Configurable (default: *)
- `Access-Control-Allow-Headers`: Content-Type, Authorization
- `Access-Control-Allow-Methods`: GET, POST, OPTIONS

## Security Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'; ...`

## JavaScript SDK Usage

```javascript
class QuickBooksAPI {
  constructor(apiKey, baseUrl) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async chat(message, options = {}) {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        message,
        use_rag: options.useRag ?? true,
        max_length: options.maxLength ?? 300,
        temperature: options.temperature ?? 0.7
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  async search(query, options = {}) {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        query,
        top_k: options.topK ?? 5,
        min_score: options.minScore ?? 0.5
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Usage
const api = new QuickBooksAPI('your-api-key', 'https://your-api-url.com/prod');

// Chat with AI
const chatResponse = await api.chat('How do I reconcile my bank account?');
console.log(chatResponse.response);

// Search knowledge base
const searchResults = await api.search('payroll setup');
console.log(searchResults.results);
```

## Python SDK Usage

```python
import requests
import json

class QuickBooksAPI:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def chat(self, message, use_rag=True, max_length=300, temperature=0.7):
        response = requests.post(
            f'{self.base_url}/chat',
            headers=self.headers,
            json={
                'message': message,
                'use_rag': use_rag,
                'max_length': max_length,
                'temperature': temperature
            }
        )
        response.raise_for_status()
        return response.json()
    
    def search(self, query, top_k=5, min_score=0.5):
        response = requests.post(
            f'{self.base_url}/search',
            headers=self.headers,
            json={
                'query': query,
                'top_k': top_k,
                'min_score': min_score
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
api = QuickBooksAPI('your-api-key', 'https://your-api-url.com/prod')

# Chat with AI
chat_response = api.chat('How do I create an invoice?')
print(chat_response['response'])

# Search knowledge base
search_results = api.search('expense tracking')
for result in search_results['results']:
    print(f"- {result['title']} (Score: {result['score']:.3f})")
```

## Webhook Support (Future)

Future versions will support webhooks for:
- New QuickBooks integrations
- Automated knowledge base updates
- Usage analytics

## OpenAPI Specification

A complete OpenAPI 3.0 specification is available at:
```
GET /openapi.json
```
