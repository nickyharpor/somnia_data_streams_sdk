"""Main SDK class for Somnia Streams."""

from typing import Optional
from web3 import Web3
from eth_account import Account

from .types import Client
from .modules import Streams
from .chains import get_default_rpc_url


class SDK:
    """Main entry point for the Somnia Streams SDK."""
    
    def __init__(self, public: Web3, wallet: Optional[Web3] = None) -> None:
        """
        Create a new SDK instance (manual configuration).
        
        Note: Manual initialization has limited write support. For write operations,
        use SDK.create_for_chain() with a private key instead.
        
        Args:
            public: Public Web3 client for reading data
            wallet: Optional wallet Web3 client for transactions
        """
        client = Client(public=public, wallet=wallet, account=None)
        self._streams = Streams(client)
    
    @classmethod
    def create_for_chain(cls, chain_id: int, private_key: Optional[str] = None) -> "SDK":
        """
        Create SDK instance using default RPC for a chain.
        
        This is the recommended way to initialize the SDK, especially for write operations.
        When a private key is provided, the SDK will automatically handle transaction signing.
        
        Args:
            chain_id: Chain ID (50312 for testnet, 5031 for mainnet)
            private_key: Optional private key for transaction signing (hex string with or without 0x prefix)
            
        Returns:
            Configured SDK instance
            
        Raises:
            ValueError: If chain ID is not supported or private key is invalid
        """
        # Get RPC URL for the chain
        rpc_url = get_default_rpc_url(chain_id)
        
        # Create public client
        public_client = Web3(Web3.HTTPProvider(rpc_url))
        
        # Initialize wallet client and account if private key is provided
        wallet_client = None
        account = None
        
        if private_key:
            try:
                # Create account from private key
                account = Account.from_key(private_key)
                
                # Create wallet client
                wallet_client = Web3(Web3.HTTPProvider(rpc_url))
                wallet_client.eth.default_account = account.address
            except Exception as e:
                raise ValueError(f"Invalid private key: {e}")
        
        # Create client with account
        client = Client(public=public_client, wallet=wallet_client, account=account)
        
        # Use internal method to create SDK instance
        return cls._from_client(client)
    
    @classmethod
    def _from_client(cls, client: Client) -> "SDK":
        """
        Internal: Create SDK from a Client instance.
        
        Args:
            client: Configured Client instance
            
        Returns:
            SDK instance
        """
        instance = cls.__new__(cls)
        instance._streams = Streams(client)
        return instance
    
    @property
    def streams(self) -> Streams:
        """
        Access the Streams module.
        
        Returns:
            Streams module instance
        """
        return self._streams
