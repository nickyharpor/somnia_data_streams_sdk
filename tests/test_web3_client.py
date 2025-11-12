"""Tests for Web3Client class."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from eth_typing import ChecksumAddress, HexStr
from web3 import Web3

from somnia_streams.services.web3_client import Web3Client
from somnia_streams.types import Client


@pytest.fixture
def mock_account():
    """Create a mock account."""
    account = Mock()
    account.address = ChecksumAddress("0x1234567890123456789012345678901234567890")
    account.sign_transaction = Mock(return_value=Mock(rawTransaction=b'\x01\x02\x03'))
    return account


@pytest.fixture
def mock_public_client():
    """Create a mock public Web3 client."""
    client = Mock(spec=Web3)
    client.eth = Mock()
    client.eth.chain_id = 50312
    client.eth.get_transaction_count = Mock(return_value=5)
    client.eth.gas_price = 1000000000
    client.eth.estimate_gas = Mock(return_value=21000)
    # Mock returns HexBytes object with hex() method
    mock_tx_hash = Mock()
    mock_tx_hash.hex.return_value = "0xabcdef"
    client.eth.send_raw_transaction = Mock(return_value=mock_tx_hash)
    client.eth.contract = Mock()
    return client


@pytest.fixture
def mock_contract():
    """Create a mock contract."""
    contract = Mock()
    function = Mock()
    function.build_transaction = Mock(return_value={
        'from': '0x1234567890123456789012345678901234567890',
        'value': 0,
        'chainId': 50312,
        'nonce': 5,
        'gasPrice': 1000000000,
    })
    function.call = Mock(return_value="test_result")
    contract.functions = Mock()
    setattr(contract.functions, 'testFunction', Mock(return_value=function))
    return contract


@pytest.mark.asyncio
async def test_write_contract_with_valid_account(mock_public_client, mock_account, mock_contract):
    """Test write_contract with a valid account."""
    # Setup
    mock_public_client.eth.contract.return_value = mock_contract
    client = Client(public=mock_public_client, account=mock_account)
    web3_client = Web3Client(client)
    
    # Execute
    tx_hash = await web3_client.write_contract(
        address=ChecksumAddress("0x1234567890123456789012345678901234567890"),
        abi=[],
        function_name="testFunction",
        args=["arg1", "arg2"],
        value=0
    )
    
    # Verify
    assert tx_hash == "0xabcdef"
    mock_public_client.eth.get_transaction_count.assert_called_once()
    mock_public_client.eth.estimate_gas.assert_called_once()
    mock_account.sign_transaction.assert_called_once()
    mock_public_client.eth.send_raw_transaction.assert_called_once()


@pytest.mark.asyncio
async def test_write_contract_without_account(mock_public_client):
    """Test write_contract without account returns None."""
    # Setup
    client = Client(public=mock_public_client, account=None)
    web3_client = Web3Client(client)
    
    # Execute
    tx_hash = await web3_client.write_contract(
        address=ChecksumAddress("0x1234567890123456789012345678901234567890"),
        abi=[],
        function_name="testFunction",
        args=[],
        value=0
    )
    
    # Verify
    assert tx_hash is None
    mock_public_client.eth.get_transaction_count.assert_not_called()


@pytest.mark.asyncio
async def test_write_contract_gas_estimation(mock_public_client, mock_account, mock_contract):
    """Test that gas estimation is called correctly."""
    # Setup
    mock_public_client.eth.contract.return_value = mock_contract
    mock_public_client.eth.estimate_gas.return_value = 50000
    client = Client(public=mock_public_client, account=mock_account)
    web3_client = Web3Client(client)
    
    # Execute
    await web3_client.write_contract(
        address=ChecksumAddress("0x1234567890123456789012345678901234567890"),
        abi=[],
        function_name="testFunction",
        args=[],
        value=0
    )
    
    # Verify gas estimation was called
    mock_public_client.eth.estimate_gas.assert_called_once()
    call_args = mock_public_client.eth.estimate_gas.call_args[0][0]
    assert 'from' in call_args
    assert 'chainId' in call_args
    assert 'nonce' in call_args


@pytest.mark.asyncio
async def test_write_contract_nonce_fetching(mock_public_client, mock_account, mock_contract):
    """Test that nonce is fetched correctly."""
    # Setup
    mock_public_client.eth.contract.return_value = mock_contract
    mock_public_client.eth.get_transaction_count.return_value = 42
    client = Client(public=mock_public_client, account=mock_account)
    web3_client = Web3Client(client)
    
    # Execute
    await web3_client.write_contract(
        address=ChecksumAddress("0x1234567890123456789012345678901234567890"),
        abi=[],
        function_name="testFunction",
        args=[],
        value=0
    )
    
    # Verify nonce was fetched for the account address
    mock_public_client.eth.get_transaction_count.assert_called_once_with(mock_account.address)


@pytest.mark.asyncio
async def test_write_contract_gas_estimation_failure(mock_public_client, mock_account, mock_contract):
    """Test that gas estimation failure raises appropriate error."""
    # Setup
    mock_public_client.eth.contract.return_value = mock_contract
    mock_public_client.eth.estimate_gas.side_effect = Exception("Insufficient funds")
    client = Client(public=mock_public_client, account=mock_account)
    web3_client = Web3Client(client)
    
    # Execute and verify
    with pytest.raises(ValueError, match="Gas estimation failed"):
        await web3_client.write_contract(
            address=ChecksumAddress("0x1234567890123456789012345678901234567890"),
            abi=[],
            function_name="testFunction",
            args=[],
            value=0
        )


@pytest.mark.asyncio
async def test_write_contract_signing_failure(mock_public_client, mock_account, mock_contract):
    """Test that transaction signing failure raises appropriate error."""
    # Setup
    mock_public_client.eth.contract.return_value = mock_contract
    mock_account.sign_transaction.side_effect = Exception("Invalid transaction")
    client = Client(public=mock_public_client, account=mock_account)
    web3_client = Web3Client(client)
    
    # Execute and verify
    with pytest.raises(ValueError, match="Transaction signing failed"):
        await web3_client.write_contract(
            address=ChecksumAddress("0x1234567890123456789012345678901234567890"),
            abi=[],
            function_name="testFunction",
            args=[],
            value=0
        )


@pytest.mark.asyncio
async def test_write_contract_broadcast_failure(mock_public_client, mock_account, mock_contract):
    """Test that transaction broadcast failure raises appropriate error."""
    # Setup
    mock_public_client.eth.contract.return_value = mock_contract
    mock_public_client.eth.send_raw_transaction.side_effect = Exception("Network error")
    client = Client(public=mock_public_client, account=mock_account)
    web3_client = Web3Client(client)
    
    # Execute and verify
    with pytest.raises(ValueError, match="Transaction broadcast failed"):
        await web3_client.write_contract(
            address=ChecksumAddress("0x1234567890123456789012345678901234567890"),
            abi=[],
            function_name="testFunction",
            args=[],
            value=0
        )


@pytest.mark.asyncio
async def test_read_contract(mock_public_client, mock_contract):
    """Test read_contract functionality."""
    # Setup
    mock_public_client.eth.contract.return_value = mock_contract
    client = Client(public=mock_public_client)
    web3_client = Web3Client(client)
    
    # Execute
    result = await web3_client.read_contract(
        address=ChecksumAddress("0x1234567890123456789012345678901234567890"),
        abi=[],
        function_name="testFunction",
        args=["arg1"]
    )
    
    # Verify
    assert result == "test_result"
    mock_public_client.eth.contract.assert_called_once()
