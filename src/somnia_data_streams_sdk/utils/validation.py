"""Address and data validation utilities."""

from eth_utils import is_address, is_same_address
from eth_typing import ChecksumAddress

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def assert_address_is_valid(
    address: str, disable_zero_address_check: bool = False
) -> None:
    """
    Validate an Ethereum address.
    
    Args:
        address: Address to validate
        disable_zero_address_check: If True, allow zero address
        
    Raises:
        ValueError: If address is invalid or zero (when not disabled)
    """
    if not is_address(address):
        raise ValueError("Invalid address")
    
    if not disable_zero_address_check and is_same_address(address, ZERO_ADDRESS):
        raise ValueError("Zero address supplied")


def is_valid_hex(value: str) -> bool:
    """
    Check if a string is a valid hex string.
    
    Args:
        value: String to check
        
    Returns:
        True if valid hex string
    """
    if not isinstance(value, str):
        return False
    
    if value.startswith("0x") or value.startswith("0X"):
        value = value[2:]
    
    try:
        int(value, 16)
        return True
    except ValueError:
        return False
