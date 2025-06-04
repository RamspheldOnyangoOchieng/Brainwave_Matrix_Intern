from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from db.db_config import db
from models.transaction import Transaction, TransactionType, TransactionStatus, TransactionCreate
from models.user import User
import logging

logger = logging.getLogger(__name__)

class ATMService:
    def __init__(self):
        self.db = db

    async def check_balance(self, account_id: UUID) -> Dict[str, Any]:
        """Check account balance"""
        try:
            account = await self.db.get_record('accounts', {'id': account_id})
            if not account:
                raise ValueError("Account not found")
            return {
                "account_id": account_id,
                "balance": account['balance'],
                "account_type": account['account_type']
            }
        except Exception as e:
            logger.error(f"Error checking balance: {str(e)}")
            raise

    async def deposit(self, account_id: UUID, amount: float, description: Optional[str] = None) -> Transaction:
        """Process deposit transaction"""
        try:
            # Get current account
            account = await self.db.get_record('accounts', {'id': account_id})
            if not account:
                raise ValueError("Account not found")
            
            # Create transaction
            transaction_data = TransactionCreate(
                account_id=account_id,
                transaction_type=TransactionType.DEPOSIT,
                amount=amount,
                description=description or "ATM Deposit"
            )
            
            # Update account balance
            new_balance = account['balance'] + amount
            await self.db.update_record('accounts', 
                {'id': account_id}, 
                {'balance': new_balance}
            )
            
            # Record transaction
            transaction = await self.db.insert_record('transactions', {
                **transaction_data.dict(),
                'balance_after': new_balance,
                'status': TransactionStatus.COMPLETED
            })
            
            return Transaction(**transaction)
        except Exception as e:
            logger.error(f"Error processing deposit: {str(e)}")
            raise

    async def withdraw(self, account_id: UUID, amount: float, description: Optional[str] = None) -> Transaction:
        """Process withdrawal transaction"""
        try:
            # Get current account
            account = await self.db.get_record('accounts', {'id': account_id})
            if not account:
                raise ValueError("Account not found")
            
            # Check sufficient balance
            if account['balance'] < amount:
                raise ValueError("Insufficient funds")
            
            # Create transaction
            transaction_data = TransactionCreate(
                account_id=account_id,
                transaction_type=TransactionType.WITHDRAWAL,
                amount=amount,
                description=description or "ATM Withdrawal"
            )
            
            # Update account balance
            new_balance = account['balance'] - amount
            await self.db.update_record('accounts', 
                {'id': account_id}, 
                {'balance': new_balance}
            )
            
            # Record transaction
            transaction = await self.db.insert_record('transactions', {
                **transaction_data.dict(),
                'balance_after': new_balance,
                'status': TransactionStatus.COMPLETED
            })
            
            return Transaction(**transaction)
        except Exception as e:
            logger.error(f"Error processing withdrawal: {str(e)}")
            raise

    async def transfer(self, from_account_id: UUID, to_account_id: UUID, amount: float, description: Optional[str] = None) -> Dict[str, Transaction]:
        """Process transfer between accounts"""
        try:
            # Get both accounts
            from_account = await self.db.get_record('accounts', {'id': from_account_id})
            to_account = await self.db.get_record('accounts', {'id': to_account_id})
            
            if not from_account or not to_account:
                raise ValueError("One or both accounts not found")
            
            # Check sufficient balance
            if from_account['balance'] < amount:
                raise ValueError("Insufficient funds")
            
            # Process withdrawal from source account
            withdrawal = await self.withdraw(
                from_account_id, 
                amount, 
                f"Transfer to {to_account['account_number']}"
            )
            
            # Process deposit to destination account
            deposit = await self.deposit(
                to_account_id, 
                amount, 
                f"Transfer from {from_account['account_number']}"
            )
            
            return {
                "withdrawal": withdrawal,
                "deposit": deposit
            }
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}")
            raise

    async def get_transaction_history(self, account_id: UUID, limit: int = 10) -> list[Transaction]:
        """Get recent transaction history"""
        try:
            transactions = await self.db.execute_query(
                """
                SELECT * FROM transactions 
                WHERE account_id = :account_id 
                ORDER BY created_at DESC 
                LIMIT :limit
                """,
                {'account_id': account_id, 'limit': limit}
            )
            return [Transaction(**t) for t in transactions]
        except Exception as e:
            logger.error(f"Error fetching transaction history: {str(e)}")
            raise

    async def validate_card(self, card_number: str, pin: str) -> Dict[str, Any]:
        """Validate ATM card and PIN"""
        try:
            card = await self.db.get_record('cards', {'card_number': card_number})
            if not card:
                raise ValueError("Invalid card")
            
            # In production, use proper password hashing
            if card['pin_hash'] != pin:  # This is just for demo
                raise ValueError("Invalid PIN")
            
            if card['status'] != 'ACTIVE':
                raise ValueError("Card is not active")
            
            account = await self.db.get_record('accounts', {'id': card['account_id']})
            if not account:
                raise ValueError("Account not found")
            
            return {
                "card_id": card['id'],
                "account_id": account['id'],
                "account_number": account['account_number']
            }
        except Exception as e:
            logger.error(f"Error validating card: {str(e)}")
            raise
