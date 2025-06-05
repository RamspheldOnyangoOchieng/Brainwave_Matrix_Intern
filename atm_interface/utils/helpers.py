import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union
from decimal import Decimal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a random salt.
    
    Args:
        password (str): The password to hash
        
    Returns:
        str: The hashed password with salt
    """
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password (str): The password to verify
        hashed_password (str): The hashed password to check against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Add logging to see the values being compared
        logger.info(f"Verifying password: Entered={password}, Hashed={hashed_password}")

        salt, stored_hash = hashed_password.split('$')
        logger.info(f"Verifying password: Salt={salt}, Stored Hash={stored_hash}")

        hash_obj = hashlib.sha256((password + salt).encode())
        calculated_hash = hash_obj.hexdigest()
        logger.info(f"Verifying password: Calculated Hash={calculated_hash}")

        return calculated_hash == stored_hash
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

def format_currency(amount: Union[float, Decimal, str]) -> str:
    """
    Format a number as currency.
    
    Args:
        amount: The amount to format
        
    Returns:
        str: Formatted currency string
    """
    try:
        amount = Decimal(str(amount))
        if amount < 0:
            return f"-${abs(amount):,.2f}"
        return f"${amount:,.2f}"
    except Exception as e:
        logger.error(f"Error formatting currency: {str(e)}")
        return "$0.00"

def validate_amount(amount: Union[float, Decimal, str]) -> bool:
    """
    Validate if an amount is positive and has at most 2 decimal places.
    
    Args:
        amount: The amount to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            return False
        # Check if amount has more than 2 decimal places
        if amount.as_tuple().exponent < -2:
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating amount: {str(e)}")
        return False

def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID.
    
    Returns:
        str: A unique transaction ID
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = secrets.token_hex(4)
    return f"TXN{timestamp}{random_part}"

def mask_card_number(card_number: str) -> str:
    """
    Mask a card number, showing only last 4 digits.
    
    Args:
        card_number (str): The card number to mask
        
    Returns:
        str: Masked card number
    """
    if not card_number or len(card_number) < 4:
        return card_number
    return f"{'*' * (len(card_number) - 4)}{card_number[-4:]}"

def format_phone_number(phone: str) -> Optional[str]:
    """
    Format a phone number to E.164 format.
    
    Args:
        phone (str): The phone number to format
        
    Returns:
        Optional[str]: Formatted phone number or None if invalid
    """
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if the number is valid
    if len(digits) < 10 or len(digits) > 15:
        return None
    
    # Add country code if not present
    if not phone.startswith('+'):
        digits = f"+1{digits}" if len(digits) == 10 else f"+{digits}"
    else:
        digits = f"+{digits}"  # Ensure + is preserved
    
    return digits

def calculate_fee(amount: Decimal, fee_percentage: float = 0.01) -> Decimal:
    """
    Calculate transaction fee.
    
    Args:
        amount (Decimal): Transaction amount
        fee_percentage (float): Fee percentage (default: 1%)
        
    Returns:
        Decimal: Calculated fee
    """
    try:
        fee = amount * Decimal(str(fee_percentage))
        # Round to 2 decimal places
        return Decimal(str(round(fee, 2)))
    except Exception as e:
        logger.error(f"Error calculating fee: {str(e)}")
        return Decimal('0.00')

def is_business_hours() -> bool:
    """
    Check if current time is within business hours (9 AM - 5 PM).
    
    Returns:
        bool: True if within business hours, False otherwise
    """
    now = datetime.now()
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
    
    return start_time <= now <= end_time

def format_timestamp(timestamp: datetime) -> str:
    """
    Format a timestamp in a human-readable format.
    
    Args:
        timestamp (datetime): The timestamp to format
        
    Returns:
        str: Formatted timestamp
    """
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email (str): Email to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_otp(length: int = 6) -> str:
    """
    Generate a one-time password.
    
    Args:
        length (int): Length of OTP (default: 6)
        
    Returns:
        str: Generated OTP
    """
    return ''.join(secrets.choice('0123456789') for _ in range(length))

def is_valid_account_number(account_number: Optional[str]) -> bool:
    """
    Validate account number format.
    
    Args:
        account_number (Optional[str]): Account number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if account_number is None:
        return False
    # Basic validation: 10 digits
    return bool(re.match(r'^\d{10}$', account_number))
