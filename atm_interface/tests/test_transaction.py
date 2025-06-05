import pytest
from uuid import uuid4
from decimal import Decimal

@pytest.fixture
def mock_account():
    return {
        'id': uuid4(),
        'balance': Decimal('1000.00'),
        'account_type': 'SAVINGS',
        'status': 'ACTIVE',
        'account_number': '1234567890'
    }
