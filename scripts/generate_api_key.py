#!/usr/bin/env python3
"""
Generate secure API keys for QuickBooks AI Agent
"""

import secrets
import string
import hashlib
import base64
import json
from datetime import datetime, timedelta

def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret(length: int = 64) -> str:
    """Generate a secure JWT secret"""
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8')

def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def main():
    """Generate API keys and configuration"""
    print("QuickBooks AI Agent - API Key Generator")
    print("=" * 50)
    
    # Generate API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Generate JWT secret
    jwt_secret = generate_jwt_secret()
    
    # Generate configuration
    config = {
        "api_key": api_key,
        "api_key_hash": api_key_hash,
        "jwt_secret": jwt_secret,
        "generated_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
    }
    
    print(f"API Key: {api_key}")
    print(f"API Key Hash: {api_key_hash}")
    print(f"JWT Secret: {jwt_secret}")
    print()
    print("Environment Variables for AWS Lambda:")
    print(f"API_KEY={api_key}")
    print(f"JWT_SECRET={jwt_secret}")
    print()
    print("GitHub Secrets to add:")
    print(f"API_KEY: {api_key}")
    print(f"JWT_SECRET: {jwt_secret}")
    print()
    
    # Save to file
    with open('api_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Configuration saved to api_config.json")
    print("⚠️  Keep this file secure and don't commit it to version control!")

if __name__ == "__main__":
    main()
