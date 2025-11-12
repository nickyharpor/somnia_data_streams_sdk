"""Tests for SDK class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from web3 import Web3
from eth_account import Account
from somnia_streams import SDK


def test_sdk_initialization():
    """Test SDK initialization."""
    public_client = Mock(spec=Web3)
    sdk = SDK(public=public_client)
    
    assert sdk.streams is not None
    assert hasattr(sdk.streams, 'get_all_schemas')


def test_sdk_with_wallet():
    """Test SDK initialization with wallet."""
    public_client = Mock(spec=Web3)
    wallet_client = Mock(spec=Web3)
    
    sdk = SDK(public=public_client, wallet=wallet_client)
    
    assert sdk.streams is not None


def test_sdk_streams_property():
    """Test streams property access."""
    public_client = Mock(spec=Web3)
    sdk = SDK(public=public_client)
    
    # Access multiple times should return same instance
    streams1 = sdk.streams
    streams2 = sdk.streams
    
    assert streams1 is streams2


@patch('somnia_streams.sdk.Web3')
@patch('somnia_streams.sdk.get_default_rpc_url')
def test_create_for_chain_with_private_key(mock_get_rpc, mock_web3_class):
    """Test SDK.create_for_chain with private key."""
    # Setup
    mock_get_rpc.return_value = "https://test-rpc.example.com"
    mock_web3_instance = Mock(spec=Web3)
    mock_web3_instance.eth = Mock()
    mock_web3_class.return_value = mock_web3_instance
    
    # Use a valid test private key
    test_private_key = "0x1234567890123456789012345678901234567890123456789012345678901234"
    
    # Execute
    sdk = SDK.create_for_chain(50312, private_key=test_private_key)
    
    # Verify
    assert sdk is not None
    assert sdk.streams is not None
    mock_get_rpc.assert_called_once_with(50312)
    assert mock_web3_class.call_count == 2  # public and wallet clients


@patch('somnia_streams.sdk.Web3')
@patch('somnia_streams.sdk.get_default_rpc_url')
def test_create_for_chain_without_private_key(mock_get_rpc, mock_web3_class):
    """Test SDK.create_for_chain without private key (read-only mode)."""
    # Setup
    mock_get_rpc.return_value = "https://test-rpc.example.com"
    mock_web3_instance = Mock(spec=Web3)
    mock_web3_instance.eth = Mock()
    mock_web3_class.return_value = mock_web3_instance
    
    # Execute
    sdk = SDK.create_for_chain(50312)
    
    # Verify
    assert sdk is not None
    assert sdk.streams is not None
    mock_get_rpc.assert_called_once_with(50312)
    assert mock_web3_class.call_count == 1  # only public client


@patch('somnia_streams.sdk.Web3')
@patch('somnia_streams.sdk.get_default_rpc_url')
def test_create_for_chain_invalid_private_key(mock_get_rpc, mock_web3_class):
    """Test SDK.create_for_chain with invalid private key."""
    # Setup
    mock_get_rpc.return_value = "https://test-rpc.example.com"
    mock_web3_instance = Mock(spec=Web3)
    mock_web3_class.return_value = mock_web3_instance
    
    # Execute and verify
    with pytest.raises(ValueError, match="Invalid private key"):
        SDK.create_for_chain(50312, private_key="invalid_key")


@patch('somnia_streams.sdk.get_default_rpc_url')
def test_create_for_chain_invalid_chain_id(mock_get_rpc):
    """Test SDK.create_for_chain with invalid chain ID."""
    # Setup
    mock_get_rpc.side_effect = ValueError("Unsupported chain ID: 99999")
    
    # Execute and verify
    with pytest.raises(ValueError, match="Unsupported chain ID"):
        SDK.create_for_chain(99999)


@patch('somnia_streams.sdk.Web3')
@patch('somnia_streams.sdk.get_default_rpc_url')
def test_create_for_chain_sets_default_account(mock_get_rpc, mock_web3_class):
    """Test that create_for_chain sets default account on wallet client."""
    # Setup
    mock_get_rpc.return_value = "https://test-rpc.example.com"
    mock_web3_instance = Mock(spec=Web3)
    mock_web3_instance.eth = Mock()
    mock_web3_class.return_value = mock_web3_instance
    
    test_private_key = "0x1234567890123456789012345678901234567890123456789012345678901234"
    
    # Execute
    sdk = SDK.create_for_chain(50312, private_key=test_private_key)
    
    # Verify that default_account was set
    # The second call to Web3 is for the wallet client
    wallet_client = mock_web3_class.return_value
    assert wallet_client.eth.default_account is not None


def test_sdk_manual_init_no_account():
    """Test that manual SDK initialization creates client without account."""
    # Setup
    public_client = Mock(spec=Web3)
    wallet_client = Mock(spec=Web3)
    
    # Execute
    sdk = SDK(public=public_client, wallet=wallet_client)
    
    # Verify
    assert sdk.streams is not None
    # The client should have no account when using manual initialization
    assert sdk._streams.web3_client.client.account is None
