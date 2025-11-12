"""Contract address mappings."""

from typing import Dict, Optional
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address

from somnia_streams.types import KnownContracts, Chains, ContractRef

ZERO_ADDRESS = to_checksum_address("0x0000000000000000000000000000000000000000")

STREAMS_LIBRARY_BY_CHAIN: Dict[Chains, ChecksumAddress] = {
    Chains.SOMNIA_MAINNET: ZERO_ADDRESS,
    Chains.SOMNIA_TESTNET: to_checksum_address("0x6AB397FF662e42312c003175DCD76EfF69D048Fc"),
}

KNOWN_CONTRACTS_BY_CHAIN: Dict[KnownContracts, Dict[str, ChecksumAddress]] = {
    KnownContracts.STREAMS: {
        str(Chains.SOMNIA_MAINNET.value): STREAMS_LIBRARY_BY_CHAIN[Chains.SOMNIA_MAINNET],
        str(Chains.SOMNIA_TESTNET.value): STREAMS_LIBRARY_BY_CHAIN[Chains.SOMNIA_TESTNET],
    },
}


async def get_contract_address(ref: ContractRef) -> Optional[ChecksumAddress]:
    """
    Get contract address from reference.
    
    Args:
        ref: Contract reference
        
    Returns:
        Contract address or None
        
    Raises:
        ValueError: If address is invalid
    """
    from eth_utils import is_address
    
    if ref.internal and ref.chain_id:
        chain_id_str = str(ref.chain_id)
        return KNOWN_CONTRACTS_BY_CHAIN[ref.internal].get(chain_id_str)
    elif ref.address:
        if not is_address(ref.address):
            raise ValueError("Invalid address supplied")
        return ref.address
    return None
