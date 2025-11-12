"""Client configuration types."""

from dataclasses import dataclass
from typing import Optional
from web3 import Web3
from eth_typing import ChecksumAddress
from eth_account.signers.local import LocalAccount

from .contracts import KnownContracts


@dataclass
class Client:
    """Container for public and wallet Web3 instances."""
    public: Web3
    wallet: Optional[Web3] = None
    account: Optional[LocalAccount] = None


@dataclass
class ContractRef:
    """Reference to a contract (internal or by address)."""
    chain_id: int
    internal: Optional[KnownContracts] = None
    address: Optional[ChecksumAddress] = None
