"""Stream-related type definitions."""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any, Dict, Union, Literal
from eth_typing import ChecksumAddress, HexStr


@dataclass
class EventParameter:
    """Event parameter definition."""
    name: str
    param_type: str
    is_indexed: bool


@dataclass
class EventSchema:
    """Event schema definition."""
    params: List[EventParameter]
    event_topic: HexStr


@dataclass
class EventStream:
    """Event stream for emission."""
    id: str
    argument_topics: List[HexStr]
    data: HexStr


@dataclass
class DataStream:
    """Data stream for publishing."""
    id: HexStr
    schema_id: HexStr
    data: HexStr


@dataclass
class DataSchemaRegistration:
    """Arguments for registering a data schema."""
    schema_name: str
    schema: str
    parent_schema_id: Optional[HexStr] = None


@dataclass
class EthCall:
    """Ethereum call specification."""
    to: ChecksumAddress
    from_: Optional[ChecksumAddress] = None
    gas: Optional[HexStr] = None
    gas_price: Optional[HexStr] = None
    value: Optional[HexStr] = None
    data: Optional[HexStr] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {"to": self.to}
        if self.from_ is not None:
            result["from"] = self.from_
        if self.gas is not None:
            result["gas"] = self.gas
        if self.gas_price is not None:
            result["gasPrice"] = self.gas_price
        if self.value is not None:
            result["value"] = self.value
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class SubscriptionInitParams:
    """Parameters for initializing a subscription."""
    eth_calls: List[EthCall]
    on_data: Callable[[Any], None]
    only_push_changes: bool
    somnia_streams_event_id: Optional[str] = None
    context: Optional[str] = None
    on_error: Optional[Callable[[Exception], None]] = None
    event_contract_source: Optional[ChecksumAddress] = None
    topic_overrides: Optional[List[HexStr]] = None


@dataclass
class SchemaItem:
    """Schema item for encoding/decoding."""
    name: str
    type: str
    value: Any


@dataclass
class SchemaDecodedItem:
    """Decoded schema item with metadata."""
    name: str
    type: str
    signature: str
    value: SchemaItem


@dataclass
class GetSomniaDataStreamsProtocolInfoResponse:
    """Response from protocol info query."""
    address: ChecksumAddress
    abi: List[Dict[str, Any]]
    chain_id: int


# Type aliases
SchemaID = HexStr
SchemaReference = str  # Can be literal schema or schema ID
LogTopic = Union[HexStr, List[HexStr], None]


@dataclass
class SomniaWatchFilter:
    """Filter for somnia_watch subscription."""
    address: Optional[Union[ChecksumAddress, List[ChecksumAddress]]] = None
    topics: Optional[List[LogTopic]] = None
    eth_calls: Optional[List[EthCall]] = None
    context: Optional[str] = None
    push_changes_only: Optional[bool] = None


@dataclass
class LogsFilter:
    """Filter for logs subscription."""
    address: Optional[Union[ChecksumAddress, List[ChecksumAddress]]] = None
    topics: Optional[List[LogTopic]] = None


@dataclass
class SubscriptionResult:
    """Result from a subscription."""
    subscription_id: str
    unsubscribe: Callable[[], None]


@dataclass
class RpcResponse:
    """RPC response structure."""
    jsonrpc: str
    id: int
    result: Optional[Any] = None
    error: Optional[Any] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


# Subscription parameter types for different subscription methods
@dataclass
class SubscribeParams:
    """Base subscription parameters."""
    on_data: Callable[[RpcResponse], None]
    on_error: Optional[Callable[[Any], None]] = None


@dataclass
class NewHeadsSubscribeParams(SubscribeParams):
    """Parameters for newHeads subscription."""
    params: Literal["newHeads"] = "newHeads"


@dataclass
class NewPendingTransactionsSubscribeParams(SubscribeParams):
    """Parameters for newPendingTransactions subscription."""
    params: Literal["newPendingTransactions"] = "newPendingTransactions"


@dataclass
class LogsSubscribeParams(SubscribeParams):
    """Parameters for logs subscription."""
    params: tuple[Literal["logs"], LogsFilter] = field(default_factory=lambda: ("logs", LogsFilter()))


@dataclass
class SyncingSubscribeParams(SubscribeParams):
    """Parameters for syncing subscription."""
    params: Literal["syncing"] = "syncing"


@dataclass
class SomniaWatchSubscribeParams(SubscribeParams):
    """Parameters for somnia_watch subscription."""
    params: tuple[Literal["somnia_watch"], SomniaWatchFilter] = field(default_factory=lambda: ("somnia_watch", SomniaWatchFilter()))
