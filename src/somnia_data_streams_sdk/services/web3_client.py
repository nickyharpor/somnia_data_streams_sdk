"""Web3 client wrapper."""

from typing import Any, List, Optional
from eth_typing import ChecksumAddress, HexStr
from web3.types import TxReceipt

from somnia_data_streams_sdk.types import Client


class Web3Client:
    """Abstraction layer over web3.py."""
    
    def __init__(self, client: Client, chain_id=50312) -> None:
        """
        Initialize Web3 client wrapper.
        
        Args:
            client: Client configuration with public and optional wallet Web3 instances
        """
        self.client = client
        self._chain_id: int = 0
    
    def get_chain_id(self) -> int:
        """
        Get chain ID (cached after first call).
        
        Returns:
            Chain ID
        """
        if self._chain_id == 0:
            self._chain_id = self.client.public.eth.chain_id
        return self._chain_id
    
    async def read_contract(
        self,
        address: ChecksumAddress,
        abi: List[Any],
        function_name: str,
        args: List[Any] = None,
    ) -> Any:
        """
        Read from a contract.
        
        Args:
            address: Contract address
            abi: Contract ABI
            function_name: Function to call
            args: Function arguments
            
        Returns:
            Function result
        """
        if args is None:
            args = []
        
        contract = self.client.public.eth.contract(address=address, abi=abi)
        func = getattr(contract.functions, function_name)
        return func(*args).call()
    
    async def write_contract(
        self,
        address: ChecksumAddress,
        abi: List[Any],
        function_name: str,
        args: List[Any] = None,
        value: int = 0,
    ) -> Optional[HexStr]:
        """
        Write to a contract with local transaction signing.
        
        Args:
            address: Contract address
            abi: Contract ABI
            function_name: Function to call
            args: Function arguments
            value: ETH value to send
            
        Returns:
            Transaction hash or None if no account available
        """
        # Check for account availability, return None if missing
        if not self.client.account:
            return None
        
        if args is None:
            args = []
        
        # Build transaction using contract function
        contract = self.client.public.eth.contract(address=address, abi=abi)
        func = getattr(contract.functions, function_name)
        
        # Get transaction parameters
        account_address = self.client.account.address
        chain_id = self.get_chain_id()
        
        # Fetch nonce using get_transaction_count with 'pending' to include pending transactions
        nonce = self.client.public.eth.get_transaction_count(account_address, 'pending')
        
        # Fetch gas price using eth.gas_price
        gas_price = self.client.public.eth.gas_price
        
        # Build transaction dict
        tx = func(*args).build_transaction({
            'from': account_address,
            'value': value,
            'chainId': chain_id,
            'nonce': nonce,
            'gasPrice': gas_price,
        })
        
        # Estimate gas using estimate_gas
        try:
            estimated_gas = self.client.public.eth.estimate_gas(tx)
            tx['gas'] = estimated_gas
        except Exception as e:
            raise ValueError(f"Gas estimation failed: {e}. Transaction would likely fail.")
        
        # Sign transaction using account.sign_transaction
        try:
            signed_tx = self.client.account.sign_transaction(tx)
        except Exception as e:
            raise ValueError(f"Transaction signing failed: {e}")
        
        # Broadcast using send_raw_transaction instead of send_transaction
        try:
            tx_hash = self.client.public.eth.send_raw_transaction(signed_tx.raw_transaction)
            return HexStr(tx_hash.hex())
        except Exception as e:
            raise ValueError(f"Transaction broadcast failed: {e}")
    
    async def wait_for_transaction(self, tx_hash: HexStr) -> TxReceipt:
        """
        Wait for transaction receipt.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt
        """
        return self.client.public.eth.wait_for_transaction_receipt(tx_hash)
    
    async def get_current_accounts(self) -> List[ChecksumAddress]:
        """
        Get current accounts from wallet client.
        
        Returns:
            List of account addresses
            
        Raises:
            ValueError: If no wallet client or no accounts found
        """
        if not self.client.wallet:
            raise ValueError("No wallet client")
        
        accounts: List[ChecksumAddress] = []
        
        # Try to get default account
        if self.client.wallet.eth.default_account:
            accounts.append(ChecksumAddress(self.client.wallet.eth.default_account))
        else:
            # Try to get accounts from provider
            try:
                accts = self.client.wallet.eth.accounts
                accounts = [ChecksumAddress(a) for a in accts]
            except Exception:
                pass
        
        if not accounts:
            raise ValueError("No wallets detected")
        
        return accounts
