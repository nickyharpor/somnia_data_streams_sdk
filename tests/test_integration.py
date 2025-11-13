"""Integration tests for transaction signing with local testnet.

These tests require a local Ethereum node (Ganache or Hardhat) to be running.
They test the full end-to-end flow of schema registration and data publishing.

To run these tests:
1. Install and start a local Ethereum node:
   - Ganache: `npm install -g ganache && ganache --port 8545`
   - Hardhat: `npx hardhat node`

2. Run tests with pytest:
   - All tests: `pytest python/tests/test_integration.py`
   - Skip integration tests: `pytest -m "not integration"`

Note: These tests are marked with @pytest.mark.integration and can be skipped
in CI/CD environments where a local node is not available.
"""

import pytest
import os
from web3 import Web3
from eth_account import Account

from somnia_data_streams_sdk import SDK


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def local_node_url():
    """Get local node URL from environment or use default."""
    return os.getenv("LOCAL_NODE_URL", "http://127.0.0.1:8545")


@pytest.fixture
def test_account():
    """Create a test account with a known private key."""
    # This is a well-known test private key (DO NOT use in production)
    private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    return Account.from_key(private_key)


@pytest.fixture
def check_local_node(local_node_url):
    """Check if local node is available, skip test if not."""
    try:
        web3 = Web3(Web3.HTTPProvider(local_node_url))
        if not web3.is_connected():
            pytest.skip("Local Ethereum node is not running")
        return web3
    except Exception:
        pytest.skip("Local Ethereum node is not available")


@pytest.fixture
def funded_account(check_local_node, test_account, local_node_url):
    """Ensure test account has funds."""
    web3 = check_local_node
    
    # Check if account has funds
    balance = web3.eth.get_balance(test_account.address)
    
    if balance == 0:
        # Try to fund from default account (works with Ganache/Hardhat)
        try:
            accounts = web3.eth.accounts
            if accounts:
                # Send 10 ETH to test account
                tx_hash = web3.eth.send_transaction({
                    'from': accounts[0],
                    'to': test_account.address,
                    'value': web3.to_wei(10, 'ether')
                })
                web3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            pytest.skip(f"Could not fund test account: {e}")
    
    return test_account


@pytest.fixture
def mock_streams_contract(check_local_node, funded_account):
    """Deploy a mock Streams contract for testing."""
    web3 = check_local_node
    
    # Simple contract ABI for testing
    # This is a minimal contract that mimics the Streams contract interface
    contract_abi = [
        {
            "inputs": [{"name": "schema", "type": "string"}],
            "name": "registerSchema",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"name": "key", "type": "string"}, {"name": "value", "type": "string"}],
            "name": "setData",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"name": "key", "type": "string"}],
            "name": "getData",
            "outputs": [{"name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Simple contract bytecode (stores and retrieves strings)
    contract_bytecode = "0x608060405234801561001057600080fd5b50610350806100206000396000f3fe608060405234801561001057600080fd5b50600436106100415760003560e01c80633bc5de3014610046578063693ec85e14610062578063e942b5161461007e575b600080fd5b610060600480360381019061005b91906101d4565b61009a565b005b61007c600480360381019061007791906101d4565b6100ae565b005b61009860048036038101906100939190610230565b6100c2565b005b80600080848152602001908152602001600020819055505050565b80600080848152602001908152602001600020819055505050565b806000808481526020019081526020016000208190555050565b6000604051905090565b600080fd5b600080fd5b600080fd5b600080fd5b6000601f19601f8301169050919050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052604160045260246000fd5b610149826100f8565b810181811067ffffffffffffffff8211171561016857610167610109565b5b80604052505050565b600061017b6100d9565b90506101878282610140565b919050565b600067ffffffffffffffff8211156101a7576101a6610109565b5b6101b0826100f8565b9050602081019050919050565b82818337600083830152505050565b60006101df6101da8461018c565b610171565b9050828152602081018484840111156101fb576101fa6100f3565b5b6102068482856101bd565b509392505050565b600082601f830112610223576102226100ee565b5b81356102338482602086016101cc565b91505092915050565b60008060408385031215610253576102526100e3565b5b600083013567ffffffffffffffff811115610271576102706100e8565b5b61027d8582860161020e565b925050602083013567ffffffffffffffff81111561029e5761029d6100e8565b5b6102aa8582860161020e565b915050925092905056fea2646970667358221220"
    
    try:
        # Deploy contract
        Contract = web3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
        
        # Get deployment transaction
        accounts = web3.eth.accounts
        if not accounts:
            pytest.skip("No accounts available for contract deployment")
        
        tx_hash = Contract.constructor().transact({'from': accounts[0]})
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        contract_address = tx_receipt.contractAddress
        return {
            'address': contract_address,
            'abi': contract_abi
        }
    except Exception as e:
        pytest.skip(f"Could not deploy test contract: {e}")


@pytest.mark.asyncio
async def test_schema_registration_end_to_end(local_node_url, funded_account, mock_streams_contract):
    """Test schema registration end-to-end with local testnet."""
    # This test would require a full Streams contract deployment
    # For now, we'll test the transaction signing mechanism directly
    
    from somnia_data_streams_sdk.services.web3_client import Web3Client
    from somnia_data_streams_sdk.types import Client
    from eth_typing import ChecksumAddress
    
    # Setup
    public_client = Web3(Web3.HTTPProvider(local_node_url))
    wallet_client = Web3(Web3.HTTPProvider(local_node_url))
    wallet_client.eth.default_account = funded_account.address
    
    client = Client(public=public_client, wallet=wallet_client, account=funded_account)
    web3_client = Web3Client(client)
    
    # Execute - call a simple contract function
    contract_address = ChecksumAddress(mock_streams_contract['address'])
    contract_abi = mock_streams_contract['abi']
    
    tx_hash = await web3_client.write_contract(
        address=contract_address,
        abi=contract_abi,
        function_name="registerSchema",
        args=["test_schema"],
        value=0
    )
    
    # Verify
    assert tx_hash is not None
    assert isinstance(tx_hash, str)
    assert tx_hash.startswith('0x')
    
    # Wait for transaction to be mined
    receipt = await web3_client.wait_for_transaction(tx_hash)
    assert receipt is not None
    assert receipt['status'] == 1  # Transaction succeeded


@pytest.mark.asyncio
async def test_data_publishing_end_to_end(local_node_url, funded_account, mock_streams_contract):
    """Test data publishing end-to-end with local testnet."""
    from somnia_data_streams_sdk.services.web3_client import Web3Client
    from somnia_data_streams_sdk.types import Client
    from eth_typing import ChecksumAddress
    
    # Setup
    public_client = Web3(Web3.HTTPProvider(local_node_url))
    wallet_client = Web3(Web3.HTTPProvider(local_node_url))
    wallet_client.eth.default_account = funded_account.address
    
    client = Client(public=public_client, wallet=wallet_client, account=funded_account)
    web3_client = Web3Client(client)
    
    # Execute - publish data
    contract_address = ChecksumAddress(mock_streams_contract['address'])
    contract_abi = mock_streams_contract['abi']
    
    tx_hash = await web3_client.write_contract(
        address=contract_address,
        abi=contract_abi,
        function_name="setData",
        args=["test_key", "test_value"],
        value=0
    )
    
    # Verify transaction
    assert tx_hash is not None
    receipt = await web3_client.wait_for_transaction(tx_hash)
    assert receipt['status'] == 1
    
    # Read back the data
    result = await web3_client.read_contract(
        address=contract_address,
        abi=contract_abi,
        function_name="getData",
        args=["test_key"]
    )
    
    # Verify data was stored
    assert result == "test_value"


@pytest.mark.asyncio
async def test_transaction_is_mined(local_node_url, funded_account, mock_streams_contract):
    """Verify that transactions are properly mined."""
    from somnia_data_streams_sdk.services.web3_client import Web3Client
    from somnia_data_streams_sdk.types import Client
    from eth_typing import ChecksumAddress
    
    # Setup
    public_client = Web3(Web3.HTTPProvider(local_node_url))
    wallet_client = Web3(Web3.HTTPProvider(local_node_url))
    wallet_client.eth.default_account = funded_account.address
    
    client = Client(public=public_client, wallet=wallet_client, account=funded_account)
    web3_client = Web3Client(client)
    
    # Get initial block number
    initial_block = public_client.eth.block_number
    
    # Execute transaction
    contract_address = ChecksumAddress(mock_streams_contract['address'])
    contract_abi = mock_streams_contract['abi']
    
    tx_hash = await web3_client.write_contract(
        address=contract_address,
        abi=contract_abi,
        function_name="registerSchema",
        args=["test_schema_2"],
        value=0
    )
    
    # Wait for transaction
    receipt = await web3_client.wait_for_transaction(tx_hash)
    
    # Verify transaction was mined in a new block
    assert receipt['blockNumber'] > initial_block
    assert receipt['transactionHash'].hex() == tx_hash
    
    # Verify we can get the transaction details
    tx = public_client.eth.get_transaction(tx_hash)
    assert tx is not None
    assert tx['from'].lower() == funded_account.address.lower()


@pytest.mark.asyncio
async def test_read_only_mode_without_private_key(local_node_url, mock_streams_contract):
    """Test that SDK works in read-only mode without private key."""
    from somnia_data_streams_sdk.services.web3_client import Web3Client
    from somnia_data_streams_sdk.types import Client
    from eth_typing import ChecksumAddress
    
    # Setup - no account
    public_client = Web3(Web3.HTTPProvider(local_node_url))
    client = Client(public=public_client, wallet=None, account=None)
    web3_client = Web3Client(client)
    
    # Read operations should work
    contract_address = ChecksumAddress(mock_streams_contract['address'])
    contract_abi = mock_streams_contract['abi']
    
    result = await web3_client.read_contract(
        address=contract_address,
        abi=contract_abi,
        function_name="getData",
        args=["test_key"]
    )
    
    # Should be able to read (even if empty)
    assert result is not None
    
    # Write operations should return None
    tx_hash = await web3_client.write_contract(
        address=contract_address,
        abi=contract_abi,
        function_name="setData",
        args=["key", "value"],
        value=0
    )
    
    assert tx_hash is None
