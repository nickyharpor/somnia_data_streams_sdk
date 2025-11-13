"""Contract address and ABI resolution."""

from typing import Dict, Any, List, Optional
from eth_typing import ChecksumAddress
from eth_utils import is_address, is_same_address

from somnia_data_streams_sdk.types import ContractRef, KnownContracts
from .abis import streams_abi
from .addresses.contract_addresses import get_contract_address

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


async def get_abi(ref: ContractRef) -> Optional[List[Dict[str, Any]]]:
    """
    Get ABI for a contract reference.
    
    Args:
        ref: Contract reference
        
    Returns:
        Contract ABI or None
        
    Raises:
        ValueError: If address is invalid
        NotImplementedError: If external address resolution is attempted
    """
    if ref.internal:
        if ref.internal == KnownContracts.STREAMS:
            return await streams_abi()
    elif ref.address:
        if not is_address(ref.address):
            raise ValueError("Invalid address supplied")
        raise NotImplementedError("External ABI resolution not implemented")
    return None


async def get_contract_address_and_abi(ref: ContractRef) -> Dict[str, Any]:
    """
    Get both contract address and ABI.
    
    Args:
        ref: Contract reference
        
    Returns:
        Dictionary with 'address' and 'abi' keys
        
    Raises:
        ValueError: If address or ABI cannot be resolved
    """
    abi = await get_abi(ref)
    if not abi:
        raise ValueError(f"Unable to resolve ABI for contract")
    
    address = await get_contract_address(ref)
    if not address:
        raise ValueError(f"Unable to resolve contract address")
    
    if not is_address(address):
        raise ValueError(f"Invalid contract address")
    
    if is_same_address(address, ZERO_ADDRESS):
        raise ValueError(f"No contract connected")
    
    return {"abi": abi, "address": address}
