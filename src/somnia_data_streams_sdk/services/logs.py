"""Error logging utilities."""

from typing import Optional
from web3.exceptions import ContractLogicError


def maybe_log_contract_error(e: Exception, context: str) -> Optional[Exception]:
    """
    Log contract errors with context.
    
    Args:
        e: Exception to log
        context: Context string for the error
        
    Returns:
        Error object if it's a contract error, None otherwise
    """
    if isinstance(e, ContractLogicError):
        error_name = str(e) or "UnknownError"
        print(f"Contract Error - {context}: {error_name}")
        return Exception(error_name)
    return None
