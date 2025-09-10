"""
AWS Lambda handler for QuickBooks AI Agent API
Connects frontend with SageMaker endpoint and RAG service
"""

import json
import boto3
import requests
import os
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from auth import AuthManager, RateLimiter, require_auth, apply_rate_limiting, validate_chat_input, sanitize_input, create_security_headers

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sagemaker_runtime = boto3.client('sagemaker-runtime')

# Initialize auth and rate limiting
auth_manager = AuthManager(
    jwt_secret=os.environ.get('JWT_SECRET', 'default-secret-change-me'),
    api_key_hash=os.environ.get('API_KEY_HASH', '')
)
rate_limiter = RateLimiter()

class QuickBooksAIHandler:
    """Main handler class for the API"""
    
    def __init__(self):
        self.sagemaker_endpoint = os.environ.get('SAGEMAKER_ENDPOINT_NAME', '')
        self.rag_service_url = os.environ.get('RAG_SERVICE_URL', '')
        self.api_key = os.environ.get('API_KEY', '')
        self.cors_origin = os.environ.get('CORS_ORIGIN', '*')
        
    def create_response(self, status_code: int, body: Dict[str, Any], 
                       headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create standardized API response"""
        default_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': self.cors_origin,
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        }
        
        # Add security headers
        security_headers = create_security_headers()
        default_headers.update(security_headers)
        
        if headers:
            default_headers.update(headers)
        
        return {
            'statusCode': status_code,
            'headers': default_headers,
            'body': json.dumps(body)
        }
    
    def validate_api_key(self, event: Dict[str, Any]) -> bool:
        """Validate API key if required"""
        if not self.api_key:
            return True  # No API key required
        
        auth_header = event.get('headers', {}).get('Authorization', '')
        if auth_header.startswith('Bearer '):
            provided_key = auth_header[7:]  # Remove 'Bearer ' prefix
            return provided_key == self.api_key
        
        return False
    
    def get_rag_context(self, query: str) -> str:
        """Get relevant context from RAG service"""
        if not self.rag_service_url:
            logger.warning("RAG service URL not configured")
            return ""
        
        try:
            response = requests.post(
                f"{self.rag_service_url}/context",
                json={'query': query, 'max_tokens': 1500},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('context', '')
            else:
                logger.warning(f"RAG service returned status {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Error calling RAG service: {e}")
            return ""
    
    def call_sagemaker(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call SageMaker endpoint for inference"""
        if not self.sagemaker_endpoint:
            return {
                'error': 'SageMaker endpoint not configured',
                'response': 'Please configure the SageMaker endpoint to use AI features.'
            }
        
        try:
            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=self.sagemaker_endpoint,
                ContentType='application/json',
                Body=json.dumps(payload)
            )
            
            result = json.loads(response['Body'].read().decode())
            return result
            
        except Exception as e:
            logger.error(f"Error calling SageMaker: {e}")
            return {
                'error': str(e),
                'response': 'I apologize, but I\'m having trouble connecting to the AI service right now. Please try again later.'
            }
    
    @require_auth(auth_manager)
    @apply_rate_limiting(rate_limiter)
    def handle_chat(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat requests"""
        try:
            # Parse request body
            body = json.loads(event.get('body', '{}'))
            
            # Validate input
            is_valid, error_msg = validate_chat_input(body)
            if not is_valid:
                return self.create_response(400, {'error': error_msg})
            
            # Sanitize message
            message = sanitize_input(body.get('message', ''))
            use_rag = body.get('use_rag', True)
            
            # Prepare SageMaker payload
            payload = {
                'message': message,
                'use_rag': use_rag,
                'max_length': body.get('max_length', 300),
                'temperature': body.get('temperature', 0.7)
            }
            
            # Call SageMaker
            result = self.call_sagemaker(payload)
            
            # Add metadata
            result['timestamp'] = datetime.utcnow().isoformat()
            result['request_id'] = event.get('requestContext', {}).get('requestId', 'unknown')
            
            return self.create_response(200, result)
            
        except Exception as e:
            logger.error(f"Error in chat handler: {e}")
            return self.create_response(500, {
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            })
    
    @require_auth(auth_manager)
    @apply_rate_limiting(rate_limiter)
    def handle_rag_search(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RAG search requests"""
        try:
            body = json.loads(event.get('body', '{}'))
            query = sanitize_input(body.get('query', ''))
            
            if not query:
                return self.create_response(400, {'error': 'Query is required'})
            
            if not self.rag_service_url:
                return self.create_response(503, {
                    'error': 'RAG service not configured',
                    'message': 'RAG search functionality is not available'
                })
            
            # Call RAG service
            try:
                response = requests.post(
                    f"{self.rag_service_url}/search",
                    json={
                        'query': query,
                        'top_k': body.get('top_k', 5),
                        'min_score': body.get('min_score', 0.5)
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    return self.create_response(200, response.json())
                else:
                    return self.create_response(response.status_code, {
                        'error': 'RAG service error',
                        'message': f'Service returned status {response.status_code}'
                    })
                    
            except requests.Timeout:
                return self.create_response(504, {
                    'error': 'RAG service timeout',
                    'message': 'The search request timed out'
                })
            except Exception as e:
                logger.error(f"Error calling RAG service: {e}")
                return self.create_response(503, {
                    'error': 'RAG service unavailable',
                    'message': 'Could not connect to the knowledge base'
                })
                
        except Exception as e:
            logger.error(f"Error in RAG search handler: {e}")
            return self.create_response(500, {
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            })
    
    def handle_health(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check requests"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {
                'sagemaker': 'configured' if self.sagemaker_endpoint else 'not_configured',
                'rag': 'configured' if self.rag_service_url else 'not_configured'
            }
        }
        
        return self.create_response(200, health_status)
    
    def handle_options(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CORS preflight requests"""
        return self.create_response(200, {}, {
            'Access-Control-Allow-Origin': self.cors_origin,
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        })

# Initialize handler
handler = QuickBooksAIHandler()

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Main Lambda handler function"""
    try:
        # Log the incoming event (excluding sensitive data)
        logger.info(f"Received {event.get('httpMethod', 'UNKNOWN')} request to {event.get('path', 'unknown')}")
        
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return handler.handle_options(event)
        
        # Validate API key if required
        if not handler.validate_api_key(event):
            return handler.create_response(401, {
                'error': 'Unauthorized',
                'message': 'Valid API key required'
            })
        
        # Route requests based on path
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        if path == '/health' and method == 'GET':
            return handler.handle_health(event)
        elif path == '/chat' and method == 'POST':
            return handler.handle_chat(event)
        elif path == '/search' and method == 'POST':
            return handler.handle_rag_search(event)
        else:
            return handler.create_response(404, {
                'error': 'Not found',
                'message': f'Path {path} not found'
            })
            
    except Exception as e:
        logger.error(f"Unhandled error in lambda_handler: {e}")
        return handler.create_response(500, {
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        })

# For local testing
if __name__ == "__main__":
    # Mock event for testing
    test_event = {
        'httpMethod': 'POST',
        'path': '/chat',
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'How do I connect my bank account to QuickBooks?',
            'use_rag': True
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
