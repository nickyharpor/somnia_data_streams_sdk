"""Contract-related type definitions."""

from enum import Enum
from typing import Dict
from eth_typing import ChecksumAddress


class KnownContracts(Enum):
    """Enum for known contract types."""
    STREAMS = "STREAMS"


class Chains(Enum):
    """Supported Somnia chain IDs."""
    SOMNIA_TESTNET = "50312"
    SOMNIA_MAINNET = "5031"


CHAIN_ID_NAME: Dict[str, str] = {
    "50312": "SomniaTestnet",
    "5031": "SomniaMainnet",
}


ContractAddressByChain = Dict[Chains, ChecksumAddress]
