"""
Authentication Manager for WAMems
Handles admin authentication for admin@cig.chat
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any

class AuthManager:
    def __init__(self, secret_key: str, admin_email: str, admin_password_hash: str):
        self.secret_key = secret_key
        self.admin_email = admin_email
        self.admin_password_hash = admin_password_hash
        self.token_expiry = timedelta(hours=24)  # 24 hours token expiry
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, password_hash = stored_hash.split(':')
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == password_hash
        except ValueError:
            return False
    
    def generate_token(self, email: str) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            'email': email,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow(),
            'iss': 'wamems'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def authenticate(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return token if successful"""
        if email != self.admin_email:
            return None
        
        if not self.verify_password(password, self.admin_password_hash):
            return None
        
        return self.generate_token(email)
    
    def require_auth(self, f):
        """Decorator to require authentication for endpoints"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            
            # Get token from cookie as fallback
            if not token:
                token = request.cookies.get('auth_token')
            
            if not token:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please provide a valid authentication token'
                }), 401
            
            payload = self.verify_token(token)
            if not payload:
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Token is expired or invalid'
                }), 401
            
            # Add user info to request context
            request.current_user = payload
            return f(*args, **kwargs)
        
        return decorated_function
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user from request context"""
        return getattr(request, 'current_user', None)

# Global auth manager instance
auth_manager = None

def init_auth_manager(secret_key: str, admin_email: str, admin_password_hash: str):
    """Initialize global auth manager"""
    global auth_manager
    auth_manager = AuthManager(secret_key, admin_email, admin_password_hash)
    return auth_manager

def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    if auth_manager is None:
        raise RuntimeError("Auth manager not initialized")
    return auth_manager

# Convenience functions
def require_auth(f):
    """Decorator to require authentication"""
    return get_auth_manager().require_auth(f)

def get_current_user():
    """Get current user"""
    return get_auth_manager().get_current_user()



















