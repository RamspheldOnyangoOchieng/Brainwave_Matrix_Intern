from functools import wraps
from flask import request, jsonify
from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, ValidationError

def validate_request(schema: Optional[BaseModel] = None, query_params: Optional[BaseModel] = None):
    """
    Decorator to validate request body and query parameters using Pydantic models.
    
    Args:
        schema: Pydantic model for request body validation
        query_params: Pydantic model for query parameters validation
    """
    def decorator(f: Callable):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                # Validate request body if schema is provided
                if schema and request.is_json:
                    data = request.get_json()
                    validated_data = schema(**data)
                    request.validated_data = validated_data
                
                # Validate query parameters if schema is provided
                if query_params:
                    validated_params = query_params(**request.args)
                    request.validated_params = validated_params
                
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify({"error": "Validation error", "details": e.errors()}), 400
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        return decorated
    return decorator

# Common validation schemas
class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 10

class DateRangeParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class AmountSchema(BaseModel):
    amount: float

class TransferSchema(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float 