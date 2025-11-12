"""Somnia Data Streams Python SDK.

A Python SDK for Somnia streams with first class reactivity support.
"""

from .sdk import SDK
from .constants import ZERO_BYTES32
from .modules import SchemaEncoder
from .chains import SOMNIA_TESTNET, SOMNIA_MAINNET, get_chain_config, get_default_rpc_url
from .types import (
    SubscriptionInitParams,
    SchemaItem,
    SchemaDecodedItem,
    EventParameter,
    EventSchema,
    EventStream,
    DataStream,
    DataSchemaRegistration,
    EthCall,
)

__version__ = "0.9.5"

__all__ = [
    "SDK",
    "ZERO_BYTES32",
    "SchemaEncoder",
    "SOMNIA_TESTNET",
    "SOMNIA_MAINNET",
    "get_chain_config",
    "get_default_rpc_url",
    "SubscriptionInitParams",
    "SchemaItem",
    "SchemaDecodedItem",
    "EventParameter",
    "EventSchema",
    "EventStream",
    "DataStream",
    "DataSchemaRegistration",
    "EthCall",
]
