from functools import wraps
from flask import request, jsonify
import time
from typing import Optional, Tuple, Dict
from collections import defaultdict
import asyncio

# In-memory storage for rate limiting
rate_limit_store: Dict[str, Dict[str, int]] = defaultdict(dict)
rate_limit_lock = asyncio.Lock()

class RateLimitExceeded(Exception):
    pass

async def get_client_identifier() -> str:
    """Get a unique identifier for the client"""
    # Use X-Forwarded-For if available, otherwise use remote_addr
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr

async def check_rate_limit(key: str, limit: int, window: int) -> Tuple[bool, int]:
    """
    Check if a request is within rate limits
    
    Args:
        key: Unique key for the rate limit
        limit: Maximum number of requests allowed in the window
        window: Time window in seconds
    
    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    current = int(time.time())
    window_key = f"{key}:{current // window}"

    async with rate_limit_lock:
        # Clean up old entries
        for k in list(rate_limit_store[key].keys()):
            try:
                window_num = int(k.split(':')[1])
                if window_num < current // window:
                    del rate_limit_store[key][k]
            except (ValueError, IndexError):
                # If there's any error parsing the key, remove it
                del rate_limit_store[key][k]

        # Get current count
        count = rate_limit_store[key].get(window_key, 0)
        
        if count >= limit:
            return False, 0
        
        # Increment count
        rate_limit_store[key][window_key] = count + 1
        return True, limit - (count + 1)

def rate_limit(limit: int = 60, window: int = 60):
    """
    Decorator to rate limit requests.
    
    Args:
        limit: Maximum number of requests allowed in the window
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            client_id = asyncio.run(get_client_identifier())
            key = f"rate_limit:{client_id}:{f.__name__}"
            
            is_allowed, remaining = asyncio.run(check_rate_limit(key, limit, window))
            
            if not is_allowed:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": window
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)

            # Handle synchronous response
            if isinstance(response, tuple):
                response_obj, status_code = response
                response_obj.headers['X-RateLimit-Limit'] = str(limit)
                response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
                response_obj.headers['X-RateLimit-Reset'] = str(int(time.time()) + window)
                return response_obj, status_code
            else:
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int(time.time()) + window)
                return response
        
        return decorated
    return decorator 