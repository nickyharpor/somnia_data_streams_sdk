"""Somnia chain definitions."""

from typing import Dict, Any

# Somnia Testnet Chain Definition
SOMNIA_TESTNET = {
    "id": 50312,
    "name": "Somnia Testnet",
    "network": "somnia-testnet",
    "nativeCurrency": {
        "name": "Somnia",
        "symbol": "STT",
        "decimals": 18,
    },
    "rpcUrls": {
        "default": {
            "http": ["https://rpc.ankr.com/somnia_testnet", "https://dream-rpc.somnia.network"],
            "webSocket": ["wss://dream-rpc.somnia.network/ws"],
        },
        "public": {
            "http": ["https://rpc.ankr.com/somnia_testnet", "https://dream-rpc.somnia.network"],
            "webSocket": ["wss://dream-rpc.somnia.network/ws"],
        },
    },
    "blockExplorers": {
        "default": {
            "name": "Somnia Testnet Explorer",
            "url": "https://shannon-explorer.somnia.network",
        }
    },
    "testnet": True,
}

# Somnia Mainnet Chain Definition
SOMNIA_MAINNET = {
    "id": 5031,
    "name": "Somnia Mainnet",
    "network": "somnia-mainnet",
    "nativeCurrency": {
        "name": "Somnia",
        "symbol": "SOMI",
        "decimals": 18,
    },
    "rpcUrls": {
        "default": {
            "http": ["https://rpc.somnia.network"],
            "webSocket": ["wss://ws.somnia.network"],
        },
        "public": {
            "http": ["https://rpc.somnia.network"],
            "webSocket": ["wss://ws.somnia.network"],
        },
    },
    "blockExplorers": {
        "default": {
            "name": "Somnia Explorer",
            "url": "https://explorer.somnia.network",
        }
    },
    "testnet": False,
}


def get_chain_config(chain_id: int) -> Dict[str, Any]:
    """
    Get chain configuration by chain ID.
    
    Args:
        chain_id: Chain ID (50312 for testnet, 5031 for mainnet)
        
    Returns:
        Chain configuration dictionary
        
    Raises:
        ValueError: If chain ID is not supported
    """
    if chain_id == 50312:
        return SOMNIA_TESTNET
    elif chain_id == 5031:
        return SOMNIA_MAINNET
    else:
        raise ValueError(f"Unsupported chain ID: {chain_id}")


def get_default_rpc_url(chain_id: int) -> str:
    """
    Get default RPC URL for a chain.
    
    Args:
        chain_id: Chain ID
        
    Returns:
        Default RPC URL
    """
    chain = get_chain_config(chain_id)
    return chain["rpcUrls"]["default"]["http"][0]
