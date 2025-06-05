from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TransactionCategory(str, Enum):
    FOOD = "FOOD"
    UTILITIES = "UTILITIES"
    ENTERTAINMENT = "ENTERTAINMENT"
    TRANSPORT = "TRANSPORT"
    SALARY = "SALARY"
    TRANSFER = "TRANSFER"
    OTHER = "OTHER"

class TransactionBase(BaseModel):
    account_id: UUID
    transaction_type: TransactionType
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    category: Optional[TransactionCategory] = TransactionCategory.OTHER

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    description: Optional[str] = None
    category: Optional[TransactionCategory] = None

class Transaction(TransactionBase):
    id: UUID
    balance_after: float
    status: TransactionStatus = TransactionStatus.COMPLETED
    created_at: datetime

    class Config:
        from_attributes = True

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2)

    @validator('balance_after')
    def validate_balance(cls, v):
        return round(v, 2)

class TransactionResponse(BaseModel):
    transaction: Transaction
    message: str
