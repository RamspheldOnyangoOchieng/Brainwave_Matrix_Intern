from flask import Flask, jsonify, request, render_template
from models.user import UserCreate, User, User as UserModel, UserLogin
from db.db_config import db
from utils.helpers import hash_password
from services.atm_service import ATMService
from utils.auth import login_required, create_access_token, verify_credentials, generate_reset_token, reset_password
from utils.validation import validate_request, PaginationParams, DateRangeParams, AmountSchema, TransferSchema
from utils.rate_limit import rate_limit
from uuid import UUID
from typing import List, Dict, Any
from datetime import datetime
from flask_swagger_ui import get_swaggerui_blueprint
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    return render_template('atm_interface.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

# --- Authentication Endpoints ---
@app.route('/auth/login', methods=['POST'])
@rate_limit(limit=5, window=300)  # 5 attempts per 5 minutes
@validate_request(schema=UserLogin)
def login():
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
    # Add logging to show received login data
    app.logger.info(f"Received login attempt for username: {data.username}")
    # Note: Avoid logging the raw PIN in production for security reasons
    # app.logger.info(f"Received login attempt for username: {data.username}, PIN: {data.pin})

    try:
        # Call verify_credentials synchronously
        user_id = verify_credentials(data.username, data.pin)
        if not user_id:
            return jsonify({"error": "Invalid credentials"}), 401
        
        token = create_access_token(user_id)
        return jsonify({"access_token": token, "token_type": "bearer"}), 200
    except Exception as e:
        app.logger.error(f"Error during login for user {data.username}: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/auth/reset-password/request', methods=['POST'])
@rate_limit(limit=3, window=3600)  # 3 attempts per hour
def request_password_reset():
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
        # Call generate_reset_token synchronously
        reset_token = generate_reset_token(email)
        if not reset_token:
            return jsonify({"error": "User not found"}), 404
        
        # In a real application, you would send this token via email
        # For demo purposes, we'll return it in the response
        return jsonify({
            "message": "Password reset token generated",
            "reset_token": reset_token  # Remove this in production
        }), 200
    except Exception as e:
        app.logger.error(f"Error requesting password reset for email {email}: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/auth/reset-password/reset', methods=['POST'])
@rate_limit(limit=3, window=3600)  # 3 attempts per hour
def reset_password_endpoint():
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
        # Call reset_password synchronously
        success = reset_password(token, new_password)
        if not success:
            return jsonify({"error": "Invalid or expired token"}), 400
        
        return jsonify({"message": "Password reset successful"}), 200
    except Exception as e:
        app.logger.error(f"Error resetting password: {str(e)}")
        return jsonify({"error": str(e)}), 400

# --- User Endpoints ---
@app.route('/users', methods=['GET', 'POST'])
@rate_limit(limit=60, window=60)  # 60 requests per minute
@validate_request(schema=UserCreate)
def users():
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
            app.logger.info("Starting user registration process.")
            # Hash the PIN before storing
            app.logger.info("Hashing password.")
            hashed_pw = hash_password(data.pin)
            app.logger.info("Password hashed successfully.")
            user_dict = data.dict()
            app.logger.info(f"User dictionary created: {user_dict}")
            user_dict['password_hash'] = hashed_pw # Store hashed PIN in password_hash column
            # Insert into DB
            # Ensure the 'id' is generated by the DB or your model defaults
            user_dict.pop('pin', None) # Remove plain PIN
            app.logger.info("Inserting user record into database.")
            # Call db.insert_record synchronously
            user_record = db.insert_record('users', user_dict)
            app.logger.info("User record inserted successfully.")
            # Remove password_hash from response for security
            user_record.pop('password_hash', None)
            app.logger.info("Registration successful, returning 201.")
            return jsonify({"user": user_record, "message": "User created successfully."}), 201
        except Exception as e:
            app.logger.error(f"Error during user registration: {str(e)}", exc_info=True) # Log traceback
            # Check if the error is a unique constraint violation
            if "duplicate key value violates unique constraint" in str(e):
                if "users_username_key" in str(e):
                    return jsonify({"error": "Username already exists."}), 409
                if "users_email_key" in str(e):
                     return jsonify({"error": "Email address already registered."}), 409
                # Add checks for other unique constraints like phone number if applicable
                # if "users_phone_number_key" in str(e):
                #     return jsonify({"error": "Phone number already registered."}), 409

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
            # Call db.execute_query synchronously
            users = db.execute_query("SELECT id, username, full_name, email, phone_number, created_at, updated_at FROM users") # Select specific columns
            return jsonify({"users": users}), 200 # Added status code 200 for success
        except Exception as e:
            app.logger.error(f"Error fetching users: {str(e)}")
            return jsonify({"error": str(e)}), 500 # Added status code 500 for server error

@app.route('/users/<user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def user_operations(user_id):
    try:
        user_uuid = handle_uuid(user_id)
        
        if request.method == 'GET':
            # Call db.get_record synchronously
            user_record = db.get_record('users', {'id': user_uuid})
            if not user_record:
                return jsonify({"error": "User not found."}), 404
            user_record.pop('password_hash', None) # Remove password hash for security
            return jsonify({"user": user_record})
            
        elif request.method == 'PUT':
            data = request.json
            # Don't allow password updates through this endpoint
            if 'password' in data:
                return jsonify({"error": "Password cannot be updated through this endpoint"}), 400
                
            # Call db.update_record synchronously
            updated_user = db.update_record('users', {'id': user_uuid}, data)
            if not updated_user:
                return jsonify({"error": "User not found."}), 404
            updated_user.pop('password_hash', None) # Remove password hash for security
            return jsonify({"user": updated_user})
            
        elif request.method == 'DELETE':
            # Call db.delete_record synchronously
            success = db.delete_record('users', {'id': user_uuid})
            if not success:
                return jsonify({"error": "User not found."}), 404
            return jsonify({"message": "User deleted successfully"})
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error during user operations for user {user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500 # Added status code 500 for server error

# --- Account Endpoints ---
@app.route('/accounts', methods=['GET'])
@login_required
@validate_request(query_params=PaginationParams)
def list_accounts():
    try:
        params = request.validated_params
        user_id = request.user_id # Get user ID from the authenticated request
        offset = (params.page - 1) * params.per_page
        # Modify query to filter by user_id
        query = f"SELECT id, account_number, account_type, balance, status, created_at, updated_at FROM accounts WHERE user_id = :user_id LIMIT {params.per_page} OFFSET {offset}"
        query_params = {"user_id": user_id}
        # Call db.execute_query synchronously
        accounts = db.execute_query(query, query_params)
        return jsonify({"accounts": accounts}), 200 # Added status code 200 for success
    except Exception as e:
        app.logger.error(f"Error listing accounts for user {request.user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500 # Added status code 500 for server error

@app.route('/accounts/<account_id>/balance', methods=['GET'])
@login_required
def check_balance(account_id):
    try:
        account_uuid = handle_uuid(account_id)
        # Call atm_service.check_balance synchronously
        result = atm_service.check_balance(account_uuid)
        return jsonify(result), 200 # Added status code 200 for success
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error checking balance for account {account_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500 # Added status code 500 for server error

@app.route('/accounts/<account_id>/deposit', methods=['POST'])
@login_required
@validate_request(schema=AmountSchema)
def deposit(account_id):
    try:
        account_uuid = handle_uuid(account_id)
        data = request.validated_data
        # Call atm_service.deposit synchronously
        transaction = atm_service.deposit(account_uuid, data.amount)
        return jsonify(transaction.dict()), 200 # Added status code 200 for success
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error during deposit for account {account_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500 # Added status code 500 for server error

@app.route('/accounts/<account_id>/withdraw', methods=['POST'])
@login_required
@validate_request(schema=AmountSchema)
def withdraw(account_id):
    try:
        account_uuid = handle_uuid(account_id)
        data = request.validated_data
        # Call atm_service.withdraw synchronously
        transaction = atm_service.withdraw(account_uuid, data.amount)
        return jsonify(transaction.dict()), 200 # Added status code 200 for success
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error during withdrawal for account {account_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500 # Added status code 500 for server error

@app.route('/accounts/transfer', methods=['POST'])
@login_required
@validate_request(schema=TransferSchema)
def transfer():
    try:
        data = request.validated_data
        from_uuid = handle_uuid(data.from_account_id)
        to_uuid = handle_uuid(data.to_account_id)
        # Call atm_service.transfer synchronously
        result = atm_service.transfer(from_uuid, to_uuid, data.amount)
        return jsonify({
            "withdrawal": result['withdrawal'].dict(),
            "deposit": result['deposit'].dict()
        }), 200 # Added status code 200 for success
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error during transfer: {str(e)}")
        return jsonify({"error": str(e)}), 500 # Added status code 500 for server error

@app.route('/accounts/<account_id>/history', methods=['GET'])
@login_required
@validate_request(query_params=DateRangeParams)
def account_history(account_id):
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
        
        # Call db.execute_query synchronously
        history = db.execute_query(query, query_params)
        # Sort history by created_at in descending order
        history.sort(key=lambda x: x['created_at'], reverse=True)

        return jsonify({"history": history}), 200 # Added status code 200 for success
    except Exception as e:
        app.logger.error(f"Error fetching account history for account {account_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500 # Added status code 500 for server error

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
        yaml.dump(swagger_yaml, f, default_flow_style=False)
    
    app.run(debug=True, host='0.0.0.0')
