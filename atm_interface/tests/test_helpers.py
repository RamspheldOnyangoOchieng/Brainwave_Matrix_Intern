import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from utils.helpers import (
    hash_password, verify_password, format_currency, validate_amount,
    generate_transaction_id, mask_card_number, format_phone_number,
    calculate_fee, is_business_hours, format_timestamp, validate_email,
    generate_otp, is_valid_account_number
)

def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPass123!"
    hashed = hash_password(password)
    
    # Test successful verification
    assert verify_password(password, hashed) is True
    
    # Test failed verification
    assert verify_password("WrongPass123!", hashed) is False
    
    # Test invalid hash format
    assert verify_password(password, "invalid_hash") is False

def test_format_currency():
    """Test currency formatting"""
    assert format_currency(1000.50) == "$1,000.50"
    assert format_currency("1000.50") == "$1,000.50"
    assert format_currency(Decimal("1000.50")) == "$1,000.50"
    assert format_currency(0) == "$0.00"
    assert format_currency(-100) == "-$100.00"
    
    # Test invalid input
    assert format_currency("invalid") == "$0.00"

def test_validate_amount():
    """Test amount validation"""
    assert validate_amount(100.50) is True
    assert validate_amount("100.50") is True
    assert validate_amount(Decimal("100.50")) is True
    assert validate_amount(0) is False
    assert validate_amount(-100) is False
    assert validate_amount(100.555) is False  # More than 2 decimal places
    assert validate_amount("invalid") is False

def test_generate_transaction_id():
    """Test transaction ID generation"""
    tx_id = generate_transaction_id()
    assert tx_id.startswith("TXN")
    assert len(tx_id) > 20  # Should be reasonably long

def test_mask_card_number():
    """Test card number masking"""
    assert mask_card_number("1234567890123456") == "************3456"
    assert mask_card_number("1234") == "1234"  # Too short to mask
    assert mask_card_number("") == ""
    assert mask_card_number(None) is None

def test_format_phone_number():
    """Test phone number formatting"""
    assert format_phone_number("1234567890") == "+11234567890"
    assert format_phone_number("+11234567890") == "+11234567890"
    assert format_phone_number("(123) 456-7890") == "+11234567890"
    assert format_phone_number("123") is None  # Too short
    assert format_phone_number("") is None
    assert format_phone_number(None) is None

def test_calculate_fee():
    """Test fee calculation"""
    assert calculate_fee(Decimal("100.00")) == Decimal("1.00")  # 1% default
    assert calculate_fee(Decimal("100.00"), 0.02) == Decimal("2.00")  # 2%
    assert calculate_fee(Decimal("0.00")) == Decimal("0.00")
    assert calculate_fee(Decimal("-100.00")) == Decimal("-1.00")

def test_is_business_hours():
    """Test business hours check"""
    # This test might need to be adjusted based on when it's run
    now = datetime.now()
    if 9 <= now.hour < 17:
        assert is_business_hours() is True
    else:
        assert is_business_hours() is False

def test_format_timestamp():
    """Test timestamp formatting"""
    timestamp = datetime(2024, 1, 1, 12, 30, 45)
    assert format_timestamp(timestamp) == "2024-01-01 12:30:45"

def test_validate_email():
    """Test email validation"""
    assert validate_email("test@example.com") is True
    assert validate_email("test.name@example.com") is True
    assert validate_email("test@example.co.uk") is True
    assert validate_email("invalid.email") is False
    assert validate_email("@example.com") is False
    assert validate_email("test@.com") is False
    assert validate_email("") is False

def test_generate_otp():
    """Test OTP generation"""
    otp = generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()
    
    # Test custom length
    otp = generate_otp(4)
    assert len(otp) == 4
    assert otp.isdigit()

def test_is_valid_account_number():
    """Test account number validation"""
    assert is_valid_account_number("1234567890") is True
    assert is_valid_account_number("123456789") is False  # Too short
    assert is_valid_account_number("12345678901") is False  # Too long
    assert is_valid_account_number("123456789a") is False  # Non-digit
    assert is_valid_account_number("") is False
    assert is_valid_account_number(None) is False 