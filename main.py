from flask import Flask, jsonify, request
from models.user import UserCreate, User, User as UserModel, UserLogin
from db.db_config import db
from utils.helpers import hash_password
from services.atm_service import ATMService
from utils.auth import login_required, create_access_token, verify_credentials, generate_reset_token, reset_password
from utils.validation import validate_request, PaginationParams, DateRangeParams, AmountSchema, TransferSchema
from utils.rate_limit import rate_limit
from uuid import UUID
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from flask_swagger_ui import get_swaggerui_blueprint
import yaml

app = Flask(__name__)
atm_service = ATMService()

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yaml'

# Create Swagger UI blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ATM Interface API"
    }
)

# Register Swagger UI blueprint
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def handle_uuid(uuid_str: str) -> UUID:
    """Helper function to handle UUID conversion with proper error handling"""
    try:
        return UUID(uuid_str)
    except ValueError:
        raise ValueError("Invalid UUID format")

@app.route('/')
def home():
    return jsonify({"message": "ATM Interface API is running."})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

# --- Authentication Endpoints ---
@app.route('/auth/login', methods=['POST'])
@rate_limit(limit=5, window=300)  # 5 attempts per 5 minutes
@validate_request(schema=UserLogin)
async def login():
    """
    Login endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
              format: password
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            access_token:
              type: string
            token_type:
              type: string
      401:
        description: Invalid credentials
    """
    data = request.validated_data
    try:
        # Await the async function directly
        user_id = await verify_credentials(data.username, data.password)
        if not user_id:
            return jsonify({"error": "Invalid credentials"}), 401
        
        token = create_access_token(user_id)
        return jsonify({"access_token": token, "token_type": "bearer"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/auth/reset-password/request', methods=['POST'])
@rate_limit(limit=3, window=3600)  # 3 attempts per hour
async def request_password_reset():
    """
    Request password reset
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email
    responses:
      200:
        description: Reset token generated
      400:
        description: Invalid request
    """
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    try:
        # Await the async function directly
        reset_token = await generate_reset_token(email)
        if not reset_token:
            return jsonify({"error": "User not found"}), 404
        
        # In a real application, you would send this token via email
        # For demo purposes, we'll return it in the response
        return jsonify({
            "message": "Password reset token generated",
            "reset_token": reset_token  # Remove this in production
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/auth/reset-password/reset', methods=['POST'])
@rate_limit(limit=3, window=3600)  # 3 attempts per hour
async def reset_password_endpoint():
    """
    Reset password using token
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - token
            - new_password
          properties:
            token:
              type: string
            new_password:
              type: string
              format: password
    responses:
      200:
        description: Password reset successful
      400:
        description: Invalid request
    """
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not all([token, new_password]):
        return jsonify({"error": "Token and new password are required"}), 400
    
    try:
        # Await the async function directly
        success = await reset_password(token, new_password)
        if not success:
            return jsonify({"error": "Invalid or expired token"}), 400
        
        return jsonify({"message": "Password reset successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- User Endpoints ---
@app.route('/users', methods=['GET', 'POST'])
@rate_limit(limit=60, window=60)  # 60 requests per minute
@validate_request(schema=UserCreate)
async def users():
    """
    List users or create a new user
    ---
    tags:
      - Users
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 10
    responses:
      200:
        description: List of users
      201:
        description: User created
    """
    if request.method == 'POST':
        data = request.validated_data
        try:
            # Hash the password before storing
            hashed_pw = hash_password(data.password)
            user_dict = data.dict()
            user_dict['password_hash'] = hashed_pw # Corrected key to password_hash
            # Insert into DB
            # Ensure the 'id' is generated by the DB or your model defaults
            user_dict.pop('password', None) # Remove plain password
            # Await the async database call directly
            user_record = await db.insert_record('users', user_dict)
            # Remove password_hash from response
            user_record.pop('password_hash', None)
            return jsonify({"user": user_record, "message": "User created successfully."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    else:  # GET
        # Apply login_required only for GET requests
        # We need a way to apply the decorator here. Let's move the GET logic
        # to a separate function or apply the check manually.
        # A simpler approach is to check for authentication manually for GET.
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        user_id = None
        if token:
             from utils.auth import verify_token # Import inside function to avoid circular dependency
             user_id = verify_token(token)

        if not user_id:
            # If no valid token, return 401 or 403
            return jsonify({"error": "Authentication token is missing or invalid"}), 401

        # Proceed with GET logic if authenticated
        try:
            # Await the async database call directly
            users = await db.execute_query("SELECT id, username, full_name, email, phone_number, created_at, updated_at FROM users") # Select specific columns
            return jsonify({"users": users})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route('/users/<user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
async def user_operations(user_id):
    try:
        user_uuid = handle_uuid(user_id)
        
        if request.method == 'GET':
            # Await the async database call directly
            user_record = await db.get_record('users', {'id': user_uuid})
            if not user_record:
                return jsonify({"error": "User not found."}), 404
            user_record.pop('password', None)
            return jsonify({"user": user_record})
            
        elif request.method == 'PUT':
            data = request.json
            # Don't allow password updates through this endpoint
            if 'password' in data:
                return jsonify({"error": "Password cannot be updated through this endpoint"}), 400
                
            # Await the async database call directly
            updated_user = await db.update_record('users', {'id': user_uuid}, data)
            if not updated_user:
                return jsonify({"error": "User not found."}), 404
            updated_user.pop('password', None)
            return jsonify({"user": updated_user})
            
        elif request.method == 'DELETE':
            # Await the async database call directly
            success = await db.delete_record('users', {'id': user_uuid})
            if not success:
                return jsonify({"error": "User not found."}), 404
            return jsonify({"message": "User deleted successfully"})
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- Account Endpoints ---
@app.route('/accounts', methods=['GET'])
@login_required
@validate_request(query_params=PaginationParams)
async def list_accounts():
    try:
        params = request.validated_params
        offset = (params.page - 1) * params.per_page
        query = f"SELECT * FROM accounts LIMIT {params.per_page} OFFSET {offset}"
        # Await the async database call directly
        accounts = await db.execute_query(query)
        return jsonify({"accounts": accounts})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/accounts/<account_id>/balance', methods=['GET'])
@login_required
async def check_balance(account_id):
    try:
        account_uuid = handle_uuid(account_id)
        # Await the async service call directly
        result = await atm_service.check_balance(account_uuid)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/accounts/<account_id>/deposit', methods=['POST'])
@login_required
@validate_request(schema=AmountSchema)
async def deposit(account_id):
    try:
        account_uuid = handle_uuid(account_id)
        data = request.validated_data
        # Await the async service call directly
        transaction = await atm_service.deposit(account_uuid, data.amount)
        return jsonify(transaction.dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/accounts/<account_id>/withdraw', methods=['POST'])
@login_required
@validate_request(schema=AmountSchema)
async def withdraw(account_id):
    try:
        account_uuid = handle_uuid(account_id)
        data = request.validated_data
        # Await the async service call directly
        transaction = await atm_service.withdraw(account_uuid, data.amount)
        return jsonify(transaction.dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/accounts/transfer', methods=['POST'])
@login_required
@validate_request(schema=TransferSchema)
async def transfer():
    try:
        data = request.validated_data
        from_uuid = handle_uuid(data.from_account_id)
        to_uuid = handle_uuid(data.to_account_id)
        # Await the async service call directly
        result = await atm_service.transfer(from_uuid, to_uuid, data.amount)
        return jsonify({
            "withdrawal": result['withdrawal'].dict(),
            "deposit": result['deposit'].dict()
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/accounts/<account_id>/history', methods=['GET'])
@login_required
@validate_request(query_params=DateRangeParams)
async def account_history(account_id):
    try:
        account_uuid = handle_uuid(account_id)
        params = request.validated_params
        
        # Build query based on date range
        query = "SELECT * FROM transactions WHERE account_id = :account_id"
        query_params = {"account_id": account_uuid}
        
        if params.start_date:
            query += " AND created_at >= :start_date"
            query_params["start_date"] = params.start_date
        if params.end_date:
            query += " AND created_at <= :end_date"
            query_params["end_date"] = params.end_date
            
        query += " ORDER BY created_at DESC"
        
        # Await the async database call directly
        transactions = await db.execute_query(query, query_params)
        return jsonify({"transactions": transactions})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    # Create Swagger YAML file
    swagger_yaml = {
        'openapi': '3.0.0',
        'info': {
            'title': 'ATM Interface API',
            'version': '1.0.0',
            'description': 'API for ATM interface operations'
        },
        'servers': [
            {
                'url': 'http://localhost:5000',
                'description': 'Development server'
            }
        ],
        'components': {
            'securitySchemes': {
                'bearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT'
                }
            }
        },
        'security': [
            {
                'bearerAuth': []
            }
        ]
    }
    
    # Write Swagger YAML to file
    with open('static/swagger.yaml', 'w') as f:
        yaml.dump(swagger_yaml, f)
    
    app.run(debug=True)
