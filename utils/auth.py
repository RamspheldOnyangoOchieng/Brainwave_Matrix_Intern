from datetime import datetime, timedelta
from typing import Optional
import jwt
from functools import wraps
from flask import request, jsonify
from db.db_config import db
import asyncio
import os
from dotenv import load_dotenv
import secrets

# Load environment variables
load_dotenv()

# Get JWT secret from environment variable
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")  # Change this in production
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(hours=24)
RESET_TOKEN_EXPIRATION = timedelta(hours=1)

def create_access_token(user_id: str) -> str:
    """Create a JWT access token for the user."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + JWT_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_reset_token(user_id: str) -> str:
    """Create a password reset token."""
    payload = {
        "user_id": user_id,
        "type": "reset",
        "exp": datetime.utcnow() + RESET_TOKEN_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the user_id if valid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the user_id if valid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Add user_id to request context
        request.user_id = user_id
        return f(*args, **kwargs)
    
    return decorated

async def verify_credentials(email: str, password: str) -> Optional[str]:
    """Verify user credentials and return user_id if valid."""
    try:
        user = await db.get_record('users', {'email': email})
        if not user:
            return None
        
        # Verify password (assuming password is hashed)
        from utils.helpers import verify_password
        if verify_password(password, user['password']):
            return str(user['id'])
        return None
    except Exception:
        return None

async def generate_reset_token(email: str) -> Optional[str]:
    """Generate a password reset token for a user."""
    try:
        user = await db.get_record('users', {'email': email})
        if not user:
            return None
        
        # Generate a reset token
        reset_token = create_reset_token(str(user['id']))
        
        # Store the reset token in the database
        await db.update_record('users', {'id': user['id']}, {
            'reset_token': reset_token,
            'reset_token_expires': datetime.utcnow() + RESET_TOKEN_EXPIRATION
        })
        
        return reset_token
    except Exception:
        return None

async def reset_password(token: str, new_password: str) -> bool:
    """Reset a user's password using a valid reset token."""
    try:
        user_id = verify_reset_token(token)
        if not user_id:
            return False
        
        # Get user and verify token matches
        user = await db.get_record('users', {'id': user_id})
        if not user or user.get('reset_token') != token:
            return False
        
        # Check if token has expired
        if datetime.utcnow() > user.get('reset_token_expires'):
            return False
        
        # Hash new password
        from utils.helpers import hash_password
        hashed_password = hash_password(new_password)
        
        # Update password and clear reset token
        await db.update_record('users', {'id': user_id}, {
            'password': hashed_password,
            'reset_token': None,
            'reset_token_expires': None
        })
        
        return True
    except Exception:
        return False 