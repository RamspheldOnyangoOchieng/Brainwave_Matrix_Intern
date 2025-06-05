import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from services.atm_service import ATMService
from models.transaction import TransactionType, TransactionStatus
from unittest.mock import AsyncMock, patch

@pytest.fixture
def atm_service():
    return ATMService()

@pytest.fixture
def mock_account():
    return {
        'id': uuid4(),
        'balance': Decimal('1000.00'),
        'account_type': 'SAVINGS',
        'status': 'ACTIVE',
        'account_number': '1234567890'  # Added for tests
    }

@pytest.fixture
def mock_card():
    return {
        'id': uuid4(),
        'card_number': '1234567890123456',
        'pin_hash': '1234',  # In production, this would be properly hashed
        'status': 'ACTIVE',
        'account_id': uuid4()
    }

@pytest.mark.asyncio
async def test_check_balance(atm_service, mock_account):
    # Mock the database call
    with patch.object(atm_service.db, 'get_record', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_account
        
        result = await atm_service.check_balance(mock_account['id'])
        
        assert result['account_id'] == mock_account['id']
        assert result['balance'] == mock_account['balance']
        assert result['account_type'] == mock_account['account_type']

@pytest.mark.asyncio
async def test_deposit(atm_service, mock_account):
    deposit_amount = Decimal('500.00')
    expected_balance = mock_account['balance'] + deposit_amount
    
    with patch.object(atm_service.db, 'get_record', new_callable=AsyncMock) as mock_get, \
         patch.object(atm_service.db, 'update_record', new_callable=AsyncMock) as mock_update, \
         patch.object(atm_service.db, 'insert_record', new_callable=AsyncMock) as mock_insert:
        
        mock_get.return_value = mock_account
        mock_insert.return_value = {
            'id': uuid4(),
            'account_id': mock_account['id'],
            'transaction_type': TransactionType.DEPOSIT,
            'amount': deposit_amount,
            'balance_after': expected_balance,
            'status': TransactionStatus.COMPLETED,
            'description': 'ATM Deposit',
            'created_at': datetime.now()
        }
        
        transaction = await atm_service.deposit(mock_account['id'], deposit_amount)
        
        assert transaction.transaction_type == TransactionType.DEPOSIT
        assert transaction.amount == deposit_amount
        assert transaction.balance_after == expected_balance
        assert transaction.status == TransactionStatus.COMPLETED

@pytest.mark.asyncio
async def test_withdraw_sufficient_funds(atm_service, mock_account):
    withdrawal_amount = Decimal('500.00')
    expected_balance = mock_account['balance'] - withdrawal_amount
    
    with patch.object(atm_service.db, 'get_record', new_callable=AsyncMock) as mock_get, \
         patch.object(atm_service.db, 'update_record', new_callable=AsyncMock) as mock_update, \
         patch.object(atm_service.db, 'insert_record', new_callable=AsyncMock) as mock_insert:
        
        mock_get.return_value = mock_account
        mock_insert.return_value = {
            'id': uuid4(),
            'account_id': mock_account['id'],
            'transaction_type': TransactionType.WITHDRAWAL,
            'amount': withdrawal_amount,
            'balance_after': expected_balance,
            'status': TransactionStatus.COMPLETED,
            'description': 'ATM Withdrawal',
            'created_at': datetime.now()
        }
        
        transaction = await atm_service.withdraw(mock_account['id'], withdrawal_amount)
        
        assert transaction.transaction_type == TransactionType.WITHDRAWAL
        assert transaction.amount == withdrawal_amount
        assert transaction.balance_after == expected_balance
        assert transaction.status == TransactionStatus.COMPLETED

@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(atm_service, mock_account):
    withdrawal_amount = Decimal('1500.00')  # More than balance
    
    with patch.object(atm_service.db, 'get_record', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_account
        
        with pytest.raises(ValueError, match="Insufficient funds"):
            await atm_service.withdraw(mock_account['id'], withdrawal_amount)

@pytest.mark.asyncio
async def test_transfer(atm_service, mock_account):
    transfer_amount = Decimal('500.00')
    to_account = {
        'id': uuid4(),
        'balance': Decimal('2000.00'),
        'account_type': 'CHECKING',
        'status': 'ACTIVE',
        'account_number': '0987654321'
    }
    
    with patch.object(atm_service.db, 'get_record', new_callable=AsyncMock) as mock_get, \
         patch.object(atm_service.db, 'update_record', new_callable=AsyncMock) as mock_update, \
         patch.object(atm_service.db, 'insert_record', new_callable=AsyncMock) as mock_insert:
        
        # Setup mock_get to return different values for different calls
        mock_get.side_effect = [
            mock_account,  # First call: get from_account
            to_account,    # Second call: get to_account
            mock_account,  # Third call: get from_account in withdraw
            to_account     # Fourth call: get to_account in deposit
        ]
        
        # Setup mock_insert to return different values for different calls
        mock_insert.side_effect = [
            {  # Withdrawal transaction
                'id': uuid4(),
                'account_id': mock_account['id'],
                'transaction_type': TransactionType.WITHDRAWAL,
                'amount': transfer_amount,
                'balance_after': mock_account['balance'] - transfer_amount,
                'status': TransactionStatus.COMPLETED,
                'description': f"Transfer to {to_account['account_number']}",
                'created_at': datetime.now()
            },
            {  # Deposit transaction
                'id': uuid4(),
                'account_id': to_account['id'],
                'transaction_type': TransactionType.DEPOSIT,
                'amount': transfer_amount,
                'balance_after': to_account['balance'] + transfer_amount,
                'status': TransactionStatus.COMPLETED,
                'description': f"Transfer from {mock_account['account_number']}",
                'created_at': datetime.now()
            }
        ]
        
        result = await atm_service.transfer(mock_account['id'], to_account['id'], transfer_amount)
        
        assert result['withdrawal'].transaction_type == TransactionType.WITHDRAWAL
        assert result['deposit'].transaction_type == TransactionType.DEPOSIT
        assert result['withdrawal'].amount == transfer_amount
        assert result['deposit'].amount == transfer_amount
        assert result['withdrawal'].balance_after == mock_account['balance'] - transfer_amount
        assert result['deposit'].balance_after == to_account['balance'] + transfer_amount

@pytest.mark.asyncio
async def test_validate_card_valid(atm_service, mock_card, mock_account):
    with patch.object(atm_service.db, 'get_record', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [mock_card, mock_account]
        
        result = await atm_service.validate_card(mock_card['card_number'], mock_card['pin_hash'])
        
        assert result['card_id'] == mock_card['id']
        assert result['account_id'] == mock_account['id']
        assert result['account_number'] == mock_account['account_number']

@pytest.mark.asyncio
async def test_validate_card_invalid_pin(atm_service, mock_card):
    with patch.object(atm_service.db, 'get_record', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_card
        
        with pytest.raises(ValueError, match="Invalid PIN"):
            await atm_service.validate_card(mock_card['card_number'], 'wrong_pin')

@pytest.mark.asyncio
async def test_get_transaction_history(atm_service, mock_account):
    mock_transactions = [
        {
            'id': uuid4(),
            'account_id': mock_account['id'],
            'transaction_type': TransactionType.DEPOSIT,
            'amount': Decimal('100.00'),
            'balance_after': Decimal('1100.00'),
            'status': TransactionStatus.COMPLETED,
            'description': 'Test deposit',
            'created_at': datetime.now()
        }
    ]
    
    with patch.object(atm_service.db, 'execute_query', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = mock_transactions
        
        transactions = await atm_service.get_transaction_history(mock_account['id'])
        
        assert len(transactions) == 1
        assert transactions[0].transaction_type == TransactionType.DEPOSIT
        assert transactions[0].amount == Decimal('100.00')
        assert transactions[0].status == TransactionStatus.COMPLETED 