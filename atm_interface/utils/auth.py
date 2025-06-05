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
import logging
from utils.helpers import verify_password, hash_password

# Load environment variables
load_dotenv()

# Get JWT secret from environment variable
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")  # Change this in production
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(hours=24)
RESET_TOKEN_EXPIRATION = timedelta(hours=1)

logger = logging.getLogger(__name__)

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
    async def decorated(*args, **kwargs):
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
        return await f(*args, **kwargs)
    
    return decorated

def verify_credentials(username: str, pin: str) -> Optional[str]:
    """Verify user credentials and return user_id if valid."""
    try:
        # Add logging before the database call
        logger.info(f"Attempting to fetch user with username: {username}")

        # Removed await as db.get_record is now synchronous
        user = db.get_record('users', {'username': username})

        # Add logging after the database call
        if user:
            logger.info(f"User found for username {username}")
            # Add logging to see the values being compared (existing logging)
            # Note: PIN logging is disabled for security
            logger.info(f"Verifying password: Stored Hash={user.get('password_hash')}")

            # Use proper password hashing with the provided PIN
            if verify_password(pin, user['password_hash']):
                logger.info(f"Password verification successful for user {username}")
                return str(user['id'])
            else:
                logger.warning(f"Password verification failed for user {username}")
                return None
        else:
            logger.warning(f"User not found for username: {username}")
            return None
    except Exception as e:
        logger.error(f"Error verifying credentials for user {username}: {str(e)}")
        # Re-raise the exception for better error propagation
        raise

def generate_reset_token(email: str) -> Optional[str]:
    """
    Generate a password reset token for a user.
    """
    try:
        # Removed await
        user = db.get_record('users', {'email': email})
        if not user:
            return None

        # Generate a reset token
        reset_token = create_reset_token(str(user['id']))

        # Store the reset token in the database
        # Removed await
        db.update_record('users', {'id': user['id']}, {
            'reset_token': reset_token,
            'reset_token_expires': datetime.utcnow() + RESET_TOKEN_EXPIRATION
        })

        return reset_token
    except Exception:
        logger.exception("Error generating reset token") # Use exception logging to include traceback
        return None

def reset_password(token: str, new_password: str) -> bool:
    """
    Reset a user's password using a valid reset token.
    """
    try:
        user_id = verify_reset_token(token)
        if not user_id:
            return False

        # Get user and verify token matches
        # Removed await
        user = db.get_record('users', {'id': user_id})
        if not user or user.get('reset_token') != token:
            return False

        # Check if token has expired
        if datetime.utcnow() > user.get('reset_token_expires'):
            return False

        # Hash new password
        hashed_password = hash_password(new_password)

        # Update password and clear reset token
        # Removed await
        db.update_record('users', {'id': user_id}, {
            'password_hash': hashed_password,
            'reset_token': None,
            'reset_token_expires': None
        })

        return True
    except Exception:
        logger.exception("Error resetting password") # Use exception logging to include traceback
        return False 