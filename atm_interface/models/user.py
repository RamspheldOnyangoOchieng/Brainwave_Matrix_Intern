from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = None

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match("^[a-zA-Z0-9_]+$", v):
            raise ValueError('Username must be alphanumeric')
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r'^\+?1?\d{9,15}$', v):
                raise ValueError('Invalid phone number format')
        return v

class UserCreate(UserBase):
    pin: str = Field(..., min_length=4, max_length=4)

    @field_validator('pin')
    @classmethod
    def pin_digits(cls, v: str) -> str:
        if not re.match(r'^\d{4}$', v):
            raise ValueError('PIN must be a 4-digit number')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r'^\+?1?\d{9,15}$', v):
                raise ValueError('Invalid phone number format')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not re.search(r'\d', v):
                raise ValueError('Password must contain at least one number')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError('Password must contain at least one special character')
        return v

class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    user: User
    message: str

class UserLogin(BaseModel):
    username: str
    pin: str

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
