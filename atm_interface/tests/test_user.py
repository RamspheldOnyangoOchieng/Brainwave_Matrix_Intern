import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from uuid import uuid4
from datetime import datetime
from models.user import UserBase, UserCreate, UserUpdate, User, UserLogin
from pydantic import EmailStr, ValidationError

@pytest.fixture
def valid_user_data():
    return {
        'username': 'testuser123',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone_number': '+1234567890',
        'pin': '1234'
    }

@pytest.fixture
def mock_user():
    return {
        'id': uuid4(),
        'username': 'testuser123',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone_number': '+1234567890',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

def test_user_create_valid(valid_user_data):
    """Test creating a user with valid data"""
    user = UserCreate(**valid_user_data)
    assert user.username == valid_user_data['username']
    assert user.full_name == valid_user_data['full_name']
    assert user.email == valid_user_data['email']
    assert user.phone_number == valid_user_data['phone_number']
    assert user.pin == valid_user_data['pin']

def test_user_create_invalid_username():
    """Test creating a user with invalid username"""
    invalid_data = {
        'username': 'test@user',  # Contains special character
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone_number': '+1234567890',
        'pin': '1234'
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_data)
    assert 'Username must be alphanumeric' in str(exc_info.value)

def test_user_create_invalid_password():
    """Test creating a user with invalid password"""
    invalid_data = {
        'username': 'testuser123',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone_number': '+1234567890',
        'pin': 'weak'
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_data)
    assert 'PIN must be a 4-digit number' in str(exc_info.value)

def test_user_create_invalid_phone():
    """Test creating a user with invalid phone number"""
    invalid_data = {
        'username': 'testuser123',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone_number': 'invalid-phone',
        'pin': '1234'
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_data)
    assert 'Invalid phone number format' in str(exc_info.value)

def test_user_update_valid(valid_user_data):
    """Test updating a user with valid data"""
    update_data = {
        'full_name': 'Updated Name',
        'phone_number': '+1987654321'
    }
    user_update = UserUpdate(**update_data)
    assert user_update.full_name == update_data['full_name']
    assert user_update.phone_number == update_data['phone_number']
    assert user_update.email is None
    assert user_update.password is None

def test_user_update_invalid_password():
    """Test updating a user with invalid password"""
    update_data = {
        'password': 'weakpass'
    }
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(**update_data)
    assert 'Password must contain at least one uppercase letter' in str(exc_info.value)

def test_user_model(mock_user):
    """Test the User model with complete data"""
    user = User(**mock_user)
    assert user.id == mock_user['id']
    assert user.username == mock_user['username']
    assert user.full_name == mock_user['full_name']
    assert user.email == mock_user['email']
    assert user.phone_number == mock_user['phone_number']
    assert user.created_at == mock_user['created_at']
    assert user.updated_at == mock_user['updated_at']

def test_user_login():
    """Test the UserLogin model"""
    login_data = {
        'username': 'testuser123',
        'pin': '1234'
    }
    login = UserLogin(**login_data)
    assert login.username == login_data['username']
    assert login.pin == login_data['pin']

def test_user_base_optional_phone():
    """Test UserBase with optional phone number"""
    user_data = {
        'username': 'testuser123',
        'full_name': 'Test User',
        'email': 'test@example.com'
    }
    user = UserBase(**user_data)
    assert user.username == user_data['username']
    assert user.full_name == user_data['full_name']
    assert user.email == user_data['email']
    assert user.phone_number is None
