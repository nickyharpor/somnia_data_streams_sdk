"""Type definitions for Somnia Streams SDK."""

from .client import Client, ContractRef
from .contracts import KnownContracts, Chains, CHAIN_ID_NAME, ContractAddressByChain
from .streams import (
    EventParameter,
    EventSchema,
    EventStream,
    DataStream,
    DataSchemaRegistration,
    EthCall,
    SubscriptionInitParams,
    SchemaItem,
    SchemaDecodedItem,
    GetSomniaDataStreamsProtocolInfoResponse,
    SchemaID,
    SchemaReference,
)

__all__ = [
    "Client",
    "ContractRef",
    "KnownContracts",
    "Chains",
    "CHAIN_ID_NAME",
    "ContractAddressByChain",
    "EventParameter",
    "EventSchema",
    "EventStream",
    "DataStream",
    "DataSchemaRegistration",
    "EthCall",
    "SubscriptionInitParams",
    "SchemaItem",
    "SchemaDecodedItem",
    "GetSomniaDataStreamsProtocolInfoResponse",
    "SchemaID",
    "SchemaReference",
]
