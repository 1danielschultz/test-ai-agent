"""
Authentication and authorization utilities for QuickBooks AI Agent
"""

import jwt
import hashlib
import time
from typing import Dict, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """Handles authentication and authorization"""
    
    def __init__(self, jwt_secret: str, api_key_hash: str = ""):
        self.jwt_secret = jwt_secret
        self.api_key_hash = api_key_hash
        self.algorithm = "HS256"
        self.token_expiry = 3600  # 1 hour
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for comparison"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key against stored hash"""
        if not self.api_key_hash:
            return True  # No API key required
        
        return self.hash_api_key(api_key) == self.api_key_hash
    
    def generate_jwt_token(self, user_id: str, additional_claims: Dict[str, Any] = None) -> str:
        """Generate JWT token"""
        now = int(time.time())
        payload = {
            'user_id': user_id,
            'iat': now,
            'exp': now + self.token_expiry,
            'iss': 'quickbooks-ai-agent'
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.algorithm)
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def create_session_token(self, user_data: Dict[str, Any]) -> str:
        """Create session token with user data"""
        return self.generate_jwt_token(
            user_id=user_data.get('user_id', 'anonymous'),
            additional_claims={
                'session_type': 'chat',
                'permissions': user_data.get('permissions', ['chat']),
                'rate_limit': user_data.get('rate_limit', 100)
            }
        )

def require_auth(auth_manager: AuthManager):
    """Decorator for functions that require authentication"""
    def decorator(func):
        @wraps(func)
        def wrapper(event: Dict[str, Any], *args, **kwargs):
            # Extract authorization header
            headers = event.get('headers', {})
            auth_header = headers.get('Authorization', '') or headers.get('authorization', '')
            
            if not auth_header:
                return {
                    'statusCode': 401,
                    'body': '{"error": "Authorization header required"}',
                    'headers': {'Content-Type': 'application/json'}
                }
            
            # Handle Bearer token
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                
                # Try JWT first
                payload = auth_manager.validate_jwt_token(token)
                if payload:
                    event['auth_payload'] = payload
                    return func(event, *args, **kwargs)
                
                # Try API key
                if auth_manager.validate_api_key(token):
                    event['auth_payload'] = {'user_id': 'api_user', 'auth_type': 'api_key'}
                    return func(event, *args, **kwargs)
            
            return {
                'statusCode': 401,
                'body': '{"error": "Invalid authorization token"}',
                'headers': {'Content-Type': 'application/json'}
            }
        
        return wrapper
    return decorator

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}  # user_id -> [(timestamp, count)]
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
    
    def cleanup_old_requests(self):
        """Remove old request records"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff = now - 3600  # Remove requests older than 1 hour
        for user_id in list(self.requests.keys()):
            self.requests[user_id] = [
                (timestamp, count) for timestamp, count in self.requests[user_id]
                if timestamp > cutoff
            ]
            if not self.requests[user_id]:
                del self.requests[user_id]
        
        self.last_cleanup = now
    
    def is_rate_limited(self, user_id: str, limit: int = 100, window: int = 3600) -> bool:
        """Check if user is rate limited"""
        self.cleanup_old_requests()
        
        now = time.time()
        cutoff = now - window
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Count requests in the current window
        current_requests = sum(
            count for timestamp, count in self.requests[user_id]
            if timestamp > cutoff
        )
        
        if current_requests >= limit:
            return True
        
        # Add current request
        self.requests[user_id].append((now, 1))
        return False

def apply_rate_limiting(rate_limiter: RateLimiter):
    """Decorator to apply rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(event: Dict[str, Any], *args, **kwargs):
            # Get user ID from auth payload or use IP
            auth_payload = event.get('auth_payload', {})
            user_id = auth_payload.get('user_id', event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'))
            
            # Get rate limit from auth payload or use default
            rate_limit = auth_payload.get('rate_limit', 100)
            
            if rate_limiter.is_rate_limited(user_id, limit=rate_limit):
                return {
                    'statusCode': 429,
                    'body': '{"error": "Rate limit exceeded", "message": "Too many requests"}',
                    'headers': {
                        'Content-Type': 'application/json',
                        'Retry-After': '3600'
                    }
                }
            
            return func(event, *args, **kwargs)
        
        return wrapper
    return decorator

# Input validation functions
def validate_chat_input(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate chat input data"""
    if not isinstance(data, dict):
        return False, "Invalid JSON data"
    
    message = data.get('message', '').strip()
    if not message:
        return False, "Message is required"
    
    if len(message) > 2000:
        return False, "Message too long (max 2000 characters)"
    
    # Check for potential injection attempts
    suspicious_patterns = ['<script', 'javascript:', 'data:text/html', '<?php']
    message_lower = message.lower()
    if any(pattern in message_lower for pattern in suspicious_patterns):
        return False, "Invalid message content"
    
    return True, ""

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not isinstance(text, str):
        return ""
    
    # Remove control characters
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Limit length
    return sanitized[:2000]

def create_security_headers() -> Dict[str, str]:
    """Create security headers for responses"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com; font-src 'self' fonts.gstatic.com; img-src 'self' data:; connect-src 'self'"
    }
