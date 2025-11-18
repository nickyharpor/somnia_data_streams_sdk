"""Streams module - core functionality for data streams."""

from typing import List, Optional, Union, Dict, Any, Literal, Callable, overload
from eth_typing import ChecksumAddress, HexStr
from eth_utils import to_hex, keccak
import asyncio
import json
from web3.exceptions import ContractCustomError
from hexbytes import HexBytes
import traceback

from somnia_data_streams_sdk.types import (
    Client,
    ContractRef,
    KnownContracts,
    DataStream,
    EventStream,
    EventSchema,
    EventParameter,
    DataSchemaRegistration,
    SubscriptionInitParams,
    SchemaID,
    SchemaReference,
    SchemaDecodedItem,
    GetSomniaDataStreamsProtocolInfoResponse,
    EthCall,
    LogTopic,
)
from somnia_data_streams_sdk.services import Web3Client, get_contract_address_and_abi, maybe_log_contract_error
from somnia_data_streams_sdk.utils import assert_address_is_valid
from somnia_data_streams_sdk.constants import ZERO_BYTES32
from .encoder import SchemaEncoder


class Streams:
    """Core functionality for data streams."""
    
    def __init__(self, client: Client) -> None:
        """
        Initialize Streams module.
        
        Args:
            client: Client configuration
        """
        self.web3_client = Web3Client(client)
    
    async def manage_event_emitters_for_registered_streams_event(
        self,
        streams_event_id: str,
        emitter: ChecksumAddress,
        is_emitter: bool,
    ) -> Optional[HexStr]:
        """
        Adjust the accounts that can emit registered streams event schemas.
        
        Args:
            streams_event_id: Identifier of the registered streams event
            emitter: Wallet address
            is_emitter: Flag to enable or disable the emitter
            
        Returns:
            Transaction hash if successful, None on error
        """
        assert_address_is_valid(emitter)
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            return await self.web3_client.write_contract(
                contract_info["address"],
                contract_info["abi"],
                "manageEventEmitter",
                [streams_event_id, emitter, is_emitter],
            )
        except Exception as e:
            print(f"manageEventEmitter failure: {e}")
            maybe_log_contract_error(e, "Failed to manage event emitter")
            return None
    
    async def set_and_emit_events(
        self,
        data_streams: List[DataStream],
        event_streams: List[EventStream],
    ) -> Optional[HexStr]:
        """
        Publish on-chain state updates and emit associated events.
        
        Args:
            data_streams: Bytes stream array with unique keys referencing schemas
            event_streams: Somnia stream event ids and associated arguments
            
        Returns:
            Transaction hash if successful, None on error
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            # Convert dataclasses to tuples for contract call
            data_tuples = [(ds.id, ds.schema_id, ds.data) for ds in data_streams]
            event_tuples = [(es.id, es.argument_topics, es.data) for es in event_streams]
            
            return await self.web3_client.write_contract(
                contract_info["address"],
                contract_info["abi"],
                "publishDataAndEmitEvents",
                [data_tuples, event_tuples],
            )
        except Exception as e:
            print(f"publishDataAndEmitEvents failure: {e}")
            maybe_log_contract_error(e, "Failed to publish data and emit events")
            return None
    
    async def register_event_schemas(
        self,
        ids: List[str],
        schemas: List[EventSchema],
    ) -> Optional[HexStr]:
        """
        Register a set of event schemas.
        
        Args:
            ids: Arbitrary identifiers for event schemas
            schemas: Event schemas with topics and parameters
            
        Returns:
            Transaction hash if successful, None on error
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            # Process schemas - compute event selector if needed
            schemas_to_register = []
            for schema in schemas:
                event_topic = schema.event_topic
                
                # If not a hex string, compute event selector
                if not event_topic.startswith("0x") and not event_topic.startswith("0X"):
                    # Compute keccak256 hash of event signature
                    event_topic = to_hex(keccak(text=event_topic))
                
                params_tuples = [
                    (p.name, p.param_type, p.is_indexed) for p in schema.params
                ]
                schemas_to_register.append((params_tuples, event_topic))
            
            return await self.web3_client.write_contract(
                contract_info["address"],
                contract_info["abi"],
                "registerEventSchemas",
                [ids, schemas_to_register],
            )
        except ContractCustomError as e:
            # Contract reverted with custom error
            error_code = str(e.args[0]) if e.args else str(e)
            if "0x65203a95" in error_code:
                print(f"Event schema already registered or invalid parameters")
            else:
                print(f"Contract custom error: {error_code}")
            return None
        except ValueError as e:
            # Gas estimation or other transaction error
            print(f"Transaction error: {e}")
            return None
        except Exception as e:
            print(f"registerEventSchemas failure: {e}")
            maybe_log_contract_error(e, "Failed to register event schema")
            return None

    async def emit_events(
        self,
        events: List[EventStream],
    ) -> Optional[HexStr]:
        """
        Emit EVM event logs on-chain.
        
        Args:
            events: Somnia stream event ids and associated arguments
            
        Returns:
            Transaction hash if successful, None on error
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            event_tuples = [(e.id, e.argument_topics, e.data) for e in events]
            
            return await self.web3_client.write_contract(
                contract_info["address"],
                contract_info["abi"],
                "emitEvents",
                [event_tuples],
            )
        except Exception as e:
            print(f"emitEvents failure: {e}")
            maybe_log_contract_error(e, "Failed to emit events")
            return None
    
    async def compute_schema_id(self, schema: str) -> Optional[HexStr]:
        """
        Compute the bytes32 keccak256 hash of the schema.
        
        Args:
            schema: Solidity compatible schema string
            
        Returns:
            The bytes32 schema ID or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            result = await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "computeSchemaId",
                [schema],
            )
            
            # Ensure result is hex string
            if isinstance(result, bytes):
                return HexStr(to_hex(result))
            return result
        except Exception as e:
            print(f"computeSchemaId error: {e}")
        return None
    
    async def is_data_schema_registered(self, schema_id: SchemaID) -> Optional[bool]:
        """
        Check if a data schema is registered.
        
        Args:
            schema_id: Hex schema ID
            
        Returns:
            Boolean denoting registration or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            return await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "isSchemaRegistered",
                [schema_id],
            )
        except Exception as e:
            print(f"isSchemaRegistered error: {e}")
        return None
    
    async def total_publisher_data_for_schema(
        self,
        schema_id: SchemaID,
        publisher: ChecksumAddress,
    ) -> Optional[int]:
        """
        Total data points published on-chain by a specific wallet for a schema.
        
        Args:
            schema_id: Unique hex reference to the schema
            publisher: Address of the wallet that published the data
            
        Returns:
            An unsigned integer or None
        """
        assert_address_is_valid(publisher)
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            return await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "totalPublisherDataForSchema",
                [schema_id, publisher],
            )
        except Exception as e:
            print(f"totalPublisherDataForSchema error: {e}")
        return None
    
    async def get_between_range(
        self,
        schema_id: SchemaID,
        publisher: ChecksumAddress,
        start_index: int,
        end_index: int,
    ) -> Union[List[HexStr], List[List[SchemaDecodedItem]], Exception, None]:
        """
        Get data in a specified range.
        
        Args:
            schema_id: Unique hex reference to the schema
            publisher: Address of the wallet that published the data
            start_index: Start of the range (inclusive)
            end_index: End of the range (exclusive)
            
        Returns:
            Raw bytes array or decoded data array or error or None
        """
        assert_address_is_valid(publisher)
        
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            raw_data = await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "getPublisherDataForSchemaInRange",
                [schema_id, publisher, start_index, end_index],
            )
            
            return await self.deserialise_raw_data(raw_data, schema_id)
        except Exception as e:
            print(f"getBetweenRange failure: {e}")
            error = maybe_log_contract_error(e, "getBetweenRange: Failed to get data")
            if isinstance(e, Exception):
                return e
        return None
    
    async def get_at_index(
        self,
        schema_id: SchemaID,
        publisher: ChecksumAddress,
        idx: int,
    ) -> Union[List[HexStr], List[List[SchemaDecodedItem]], None]:
        """
        Read historical published data at a known index.
        
        Args:
            schema_id: Unique schema reference
            publisher: Wallet that published the data
            idx: Index of the data
            
        Returns:
            Raw data or deserialised data or None
        """
        assert_address_is_valid(publisher)
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            raw_data = await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "getPublisherDataForSchemaAtIndex",
                [schema_id, publisher, idx],
            )
            
            return await self.deserialise_raw_data([raw_data], schema_id)
        except Exception as e:
            print(f"getAtIndex error: {e}")
        return None
    
    async def parent_schema_id(self, schema_id: SchemaID) -> Optional[HexStr]:
        """
        Fetch the parent schema of another schema.
        
        Args:
            schema_id: Hex identifier of the schema
            
        Returns:
            A hex value (bytes32) or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            return await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "parentSchemaId",
                [schema_id],
            )
        except Exception as e:
            print(f"parentSchemaId error: {e}")
        return None
    
    async def schema_id_to_schema_name(self, schema_id: SchemaID) -> Optional[str]:
        """
        Query the unique human readable identifier for a schema.
        
        Args:
            schema_id: Hex encoded schema ID
            
        Returns:
            The human readable identifier or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            return await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "schemaIdToId",
                [schema_id],
            )
        except Exception as e:
            print(f"schemaIdToId error: {e}")
        return None
    
    async def schema_name_to_schema_id(self, id: str) -> Optional[bytes]:
        """
        Lookup the Hex schema ID for a human readable identifier.
        
        Args:
            id: Human readable identifier
            
        Returns:
            bytes-like object for Hex schema id or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            return await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "idToSchemaId",
                [id],
            )
        except Exception as e:
            print(f"idToSchemaId error: {e}")
        return None

    async def register_data_schemas(
        self,
        registrations: List[DataSchemaRegistration],
    ) -> Union[HexStr, Exception, None]:
        """
        Batch register multiple schemas.
        
        Args:
            registrations: Array of raw schemas and parent schemas
            
        Returns:
            Transaction hash if successful, Error or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            reg_tuples = [
                (
                    r.schema_name,
                    r.schema,
                    r.parent_schema_id if r.parent_schema_id else ZERO_BYTES32,
                )
                for r in registrations
            ]
            
            return await self.web3_client.write_contract(
                contract_info["address"],
                contract_info["abi"],
                "registerSchemas",
                [reg_tuples],
            )
        except ContractCustomError as e:
            # Contract reverted with custom error
            error_code = str(e.args[0]) if e.args else str(e)
            if "0x3e505c75" in error_code:
                print(f"Schema already registered (skipping)")
            else:
                print(f"Contract error: {error_code}")
            return None
        except ValueError as e:
            # Gas estimation or other transaction error
            print(f"Transaction error: {e}")
            return None
        except Exception as e:
            print(f"registerSchemas failure: {e}")
            maybe_log_contract_error(e, "Failed to register schemas")
            return None
    
    async def set(self, data_streams: List[DataStream]) -> Optional[HexStr]:
        """
        Write data to chain using data streams.
        
        Args:
            data_streams: Bytes stream array with unique keys
            
        Returns:
            Transaction hash or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))

            data_tuples = [(ds.id, ds.schema_id, ds.data) for ds in data_streams]

            return await self.web3_client.write_contract(
                contract_info["address"],
                contract_info["abi"],
                "esstores",
                [data_tuples],
            )
        except Exception as e:
            print(f"esstores error: {e}")
        return None
    
    async def get_all_schemas(self) -> Optional[List[str]]:
        """
        Fetch all raw, registered public schemas.
        
        Returns:
            Array of full schemas or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            return await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "getAllSchemas",
            )
        except Exception as e:
            print(f"getAllSchemas error: {e}")
        return None
    
    async def get_all_publisher_data_for_schema(
        self,
        schema_id: SchemaID,
        publisher: ChecksumAddress,
    ) -> Union[List[HexStr], List[List[SchemaDecodedItem]], None]:
        """
        Query all data published by a specific wallet for a schema.
        
        Args:
            schema_id: Unique schema reference
            publisher: Wallet that broadcast the data
            
        Returns:
            Hex array or decoded data array or None
        """
        assert_address_is_valid(publisher)
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            raw_data = await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "getAllPublisherDataForSchema",
                [schema_id, publisher],
            )
            
            return await self.deserialise_raw_data(raw_data, schema_id)
        except Exception as e:
            print(f"getAllPublisherDataForSchema error: {e}")
        return None
    
    async def get_by_key(
        self,
        schema_id: SchemaID,
        publisher: ChecksumAddress,
        key: HexStr,
    ) -> Union[List[HexStr], List[List[SchemaDecodedItem]], None]:
        """
        Read state from the Somnia streams protocol.
        
        Args:
            schema_id: Unique hex identifier for the schema
            publisher: Address of the wallet that wrote the data
            key: Unique reference to the data
            
        Returns:
            The raw or decoded data or None
        """
        assert_address_is_valid(publisher)
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            key = HexBytes(key)

            # Get the index associated with the data key
            index = await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "publisherDataIndex",
                [schema_id, publisher, key],
            )
            
            return await self.get_at_index(schema_id, publisher, index)
        except Exception as e:
            print(f"getByKey error: {e}")
        return None
    
    async def get_event_schemas_by_id(
        self,
        ids: List[str],
    ) -> Optional[List[EventSchema]]:
        """
        Get registered event schemas by identifiers.
        
        Args:
            ids: Set of event schema identifiers
            
        Returns:
            Set of event schemas or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            schemas_data = await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "getEventSchemasById",
                [ids],
            )
            
            # Convert tuple data to EventSchema objects
            result = []
            for schema_tuple in schemas_data:
                params_data, event_topic = schema_tuple
                params = [
                    EventParameter(
                        name=p[0],
                        param_type=p[1],
                        is_indexed=p[2],
                    )
                    for p in params_data
                ]
                result.append(EventSchema(params=params, event_topic=event_topic))
            
            return result
        except Exception as e:
            print(f"getEventSchemasById error: {e}")
        return None
    
    async def get_last_published_data_for_schema(
        self,
        schema_id: SchemaID,
        publisher: ChecksumAddress,
    ) -> Union[List[HexStr], List[List[SchemaDecodedItem]], None]:
        """
        Get the last published data for a schema.
        
        Args:
            schema_id: Unique schema identifier
            publisher: Wallet address of the publisher
            
        Returns:
            Raw or decoded data or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            raw_data = await self.web3_client.read_contract(
                contract_info["address"],
                contract_info["abi"],
                "getLastPublishedDataForSchema",
                [schema_id, publisher],
            )
            
            return await self.deserialise_raw_data([raw_data], schema_id)
        except Exception as e:
            print(f"getLastPublishedDataForSchema error: {e}")
        return None
    
    async def get_somnia_data_streams_protocol_info(
        self,
    ) -> Union[GetSomniaDataStreamsProtocolInfoResponse, Exception, None]:
        """
        Get protocol info based on connected client.
        
        Returns:
            Protocol info or error or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            return GetSomniaDataStreamsProtocolInfoResponse(
                address=contract_info["address"],
                abi=contract_info["abi"],
                chain_id=chain_id,
            )
        except Exception as e:
            print(f"getSomniaDataStreamsProtocolInfo error: {e}")
            if isinstance(e, Exception):
                return e
        return None

    @overload
    async def subscribe(
            self,
            params: Literal["newHeads"],
            on_data: Callable[[Dict[str, Any]], None],
            on_error: Optional[Callable[[Any], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Subscribe to new block headers."""
        ...

    @overload
    async def subscribe(
            self,
            params: Literal["newPendingTransactions"],
            on_data: Callable[[Dict[str, Any]], None],
            on_error: Optional[Callable[[Any], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Subscribe to new pending transactions."""
        ...

    @overload
    async def subscribe(
            self,
            params: tuple[Literal["logs"], Dict[str, Any]],
            on_data: Callable[[Dict[str, Any]], None],
            on_error: Optional[Callable[[Any], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Subscribe to logs with filter."""
        ...

    @overload
    async def subscribe(
            self,
            params: Literal["syncing"],
            on_data: Callable[[Dict[str, Any]], None],
            on_error: Optional[Callable[[Any], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Subscribe to syncing status."""
        ...

    @overload
    async def subscribe(
            self,
            params: tuple[Literal["somnia_watch"], Dict[str, Any]],
            on_data: Callable[[Dict[str, Any]], None],
            on_error: Optional[Callable[[Any], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Subscribe to somnia_watch events."""
        ...

    async def subscribe(
            self,
            params: Union[
                Literal["newHeads"],
                Literal["newPendingTransactions"],
                Literal["syncing"],
                tuple[Literal["logs"], Dict[str, Any]],
                tuple[Literal["somnia_watch"], Dict[str, Any]],
            ],
            on_data: Callable[[Dict[str, Any]], None],
            on_error: Optional[Callable[[Any], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Subscribe to WebSocket events with type-safe parameters.

        This method provides overloaded signatures for different subscription types:
        - "newHeads": Subscribe to new block headers
        - "newPendingTransactions": Subscribe to new pending transactions
        - ("logs", filter): Subscribe to logs with optional filter
        - "syncing": Subscribe to syncing status
        - ("somnia_watch", filter): Subscribe to Somnia watch events with filter

        Args:
            params: Subscription type and optional filter parameters
            on_data: Callback function for received data
            on_error: Optional callback function for errors

        Returns:
            Dictionary with 'subscription_id' and 'unsubscribe' callback, or None

        Example:
            # Subscribe to new heads
            await streams.subscribe("newHeads", on_data=handle_block)

            # Subscribe to logs
            await streams.subscribe(
                ("logs", {"address": contract_address}),
                on_data=handle_log
            )

            # Subscribe to somnia_watch
            await streams.subscribe(
                ("somnia_watch", {
                    "address": contract_address,
                    "topics": [event_topic],
                    "eth_calls": [call],
                    "context": "data",
                    "push_changes_only": True
                }),
                on_data=handle_event
            )
        """
        try:
            # Validate Web3 provider supports WebSocket
            if not hasattr(self.web3_client.client.public, 'provider'):
                raise ValueError("Web3 client does not have a provider")

            provider = self.web3_client.client.public.provider

            # Check if provider supports subscriptions
            if not hasattr(provider, 'make_request'):
                raise ValueError("Provider does not support subscriptions")

            # Parse subscription parameters
            subscription_method = "eth_subscribe"
            subscription_params: List[Any] = []

            if isinstance(params, str):
                # Simple subscription types: newHeads, newPendingTransactions, syncing
                subscription_params = [params]
            elif isinstance(params, tuple) and len(params) == 2:
                # Complex subscription types: logs, somnia_watch
                sub_type, filter_params = params
                subscription_params = [sub_type, filter_params]
            else:
                raise ValueError(f"Invalid subscription params: {params}")

            # Make the eth_subscribe request
            response = provider.make_request("eth_subscribe", subscription_params)

            if "error" in response:
                error_msg = response["error"].get("message", str(response["error"]))
                raise ValueError(f"Subscription failed: {error_msg}")

            subscription_id = response.get("result")
            if not subscription_id:
                raise ValueError("No subscription ID returned from provider")

            # Track if subscription is active
            is_active = True

            # Create message handler for incoming subscription messages
            async def handle_messages():
                """Listen for subscription messages and call on_data callback."""
                nonlocal is_active

                try:
                    # Check if provider has a message stream or socket
                    if hasattr(provider, '_ws') and provider._ws:
                        ws = provider._ws

                        while is_active:
                            try:
                                # Wait for message with timeout
                                message = await asyncio.wait_for(
                                    ws.recv(),
                                    timeout=30.0
                                )

                                # Parse JSON message
                                data = json.loads(message) if isinstance(message, str) else message

                                # Check if this is a subscription notification
                                if (
                                        data.get("method") == "eth_subscription"
                                        and data.get("params", {}).get("subscription") == subscription_id
                                ):
                                    # Extract the result and call on_data
                                    result = data.get("params", {}).get("result")
                                    if result is not None:
                                        on_data(result)

                            except asyncio.TimeoutError:
                                # Timeout is normal, continue listening
                                continue
                            except Exception as e:
                                if is_active and on_error:
                                    on_error(e)
                                if not is_active:
                                    break

                except Exception as e:
                    if is_active and on_error:
                        on_error(e)

            # Start message handler in background
            message_task = asyncio.create_task(handle_messages())

            # Create unsubscribe function
            async def unsubscribe():
                """Unsubscribe from the WebSocket subscription."""
                nonlocal is_active
                is_active = False

                try:
                    # Cancel message handler
                    message_task.cancel()

                    # Send eth_unsubscribe request
                    unsub_response = await provider.make_request(
                        "eth_unsubscribe",
                        [subscription_id]
                    )

                    if "error" in unsub_response:
                        print(f"Unsubscribe error: {unsub_response['error']}")
                        return False

                    return unsub_response.get("result", False)

                except Exception as e:
                    print(f"Unsubscribe failed: {e}")
                    return False

            # Return subscription info
            return {
                "subscription_id": subscription_id,
                "unsubscribe": unsubscribe,
                "_message_task": message_task,  # Keep reference to prevent GC
            }

        except Exception as e:
            if on_error:
                on_error(e)
            print(f"subscribe error: {e}")
            return None

    async def subscribe_legacy(
            self,
            init_params: SubscriptionInitParams,
    ) -> Optional[Dict[str, Any]]:
        """
        Legacy subscription method using SubscriptionInitParams.

        This method is kept for backward compatibility but the new overloaded
        subscribe() method is recommended for better type safety.

        Args:
            init_params: Subscription parameters

        Returns:
            Subscription info with subscriptionId and unsubscribe callback or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()

            contract_info = await get_contract_address_and_abi(
                ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))

            streams_protocol_address = contract_info["address"]

            # Determine event source
            event_source = (
                init_params.event_contract_source
                if init_params.event_contract_source
                else streams_protocol_address
            )
            assert_address_is_valid(event_source)

            # Determine event topics
            event_topics: List[HexStr] = []

            if event_source == streams_protocol_address:
                # Using Somnia streams as event source
                if not init_params.topic_overrides or len(init_params.topic_overrides) == 0:
                    if not init_params.somnia_streams_event_id:
                        raise ValueError("Somnia streams event ID must be specified")

                    # Fetch the topic info from the streams contract
                    event_schemas = await self.get_event_schemas_by_id(
                        [init_params.somnia_streams_event_id]
                    )
                    if not event_schemas:
                        raise ValueError("Failed to get the event schema")
                    if len(event_schemas) < 1:
                        raise ValueError("No event schema returned")
                    if len(event_schemas) > 1:
                        raise ValueError("Too many schemas found")

                    event_topic = event_schemas[0].event_topic
                    event_topics.append(event_topic)
                else:
                    event_topics = init_params.topic_overrides
            else:
                # Using custom event source
                if not init_params.topic_overrides:
                    raise ValueError("Specified event contract source but no event topic specified")
                event_topics = init_params.topic_overrides

            # Build somnia_watch filter
            somnia_watch_filter = {
                "address": event_source,
                "topics": event_topics,
                "eth_calls": [call.to_dict() for call in init_params.eth_calls],
                "context": init_params.context,
                "push_changes_only": init_params.only_push_changes,
            }

            # Use the new subscribe method
            return await self.subscribe(
                ("somnia_watch", somnia_watch_filter),
                on_data=init_params.on_data,
                on_error=init_params.on_error,
            )

        except Exception as e:
            print(f"subscribe_legacy error: {e}")
        return None

    async def subscribe_old(
        self,
        init_params: SubscriptionInitParams,
    ) -> Optional[Dict[str, Any]]:
        """
        Somnia streams reactivity enabling event subscriptions.
        
        Args:
            init_params: Subscription parameters
            
        Returns:
            Subscription info with subscriptionId and unsubscribe callback or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            streams_protocol_address = contract_info["address"]
            
            # Determine event source
            event_source = (
                init_params.event_contract_source
                if init_params.event_contract_source
                else streams_protocol_address
            )
            assert_address_is_valid(event_source)
            
            # Determine event topics
            event_topics: List[HexStr] = []
            
            if event_source == streams_protocol_address:
                # Using Somnia streams as event source
                if not init_params.topic_overrides or len(init_params.topic_overrides) == 0:
                    if not init_params.somnia_streams_event_id:
                        raise ValueError("Somnia streams event ID must be specified")
                    
                    # Fetch the topic info from the streams contract
                    event_schemas = await self.get_event_schemas_by_id(
                        [init_params.somnia_streams_event_id]
                    )
                    if not event_schemas:
                        raise ValueError("Failed to get the event schema")
                    if len(event_schemas) < 1:
                        raise ValueError("No event schema returned")
                    if len(event_schemas) > 1:
                        raise ValueError("Too many schemas found")
                    
                    event_topic = event_schemas[0].event_topic
                    event_topics.append(event_topic)
                else:
                    event_topics = init_params.topic_overrides
            else:
                # Using custom event source
                if not init_params.topic_overrides:
                    raise ValueError("Specified event contract source but no event topic specified")
                event_topics = init_params.topic_overrides
            
            # Prepare eth_calls if provided (ensure all values are JSON-serializable)
            eth_calls = []
            if init_params.eth_calls:
                eth_calls = [
                    {
                        "to": str(call.to),
                        "data": to_hex(call.data) if isinstance(call.data, bytes) else (call.data if call.data else "0x"),
                    }
                    for call in init_params.eth_calls
                ]
            
            # Prepare subscription parameters (ensure all values are JSON-serializable strings)
            subscription_params = {
                "address": str(event_source),
                "topics": [str(topic) for topic in event_topics],
            }
            
            if eth_calls:
                subscription_params["eth_calls"] = eth_calls
            
            if init_params.context:
                subscription_params["context"] = str(init_params.context)
            
            if init_params.only_push_changes is not None:
                subscription_params["push_changes_only"] = bool(init_params.only_push_changes) #type: ignore
            
            # Create WebSocket client using websockets library
            import asyncio
            import json
            from websockets.asyncio.client import connect
            
            # Get WebSocket URL from chain config
            from somnia_data_streams_sdk.chains import get_chain_config
            chain_config = get_chain_config(chain_id)
            ws_url = chain_config.get("rpcUrls", {}).get("default", {}).get("webSocket", [None])[0]
            
            if not ws_url:
                raise ValueError(f"No WebSocket URL configured for chain {chain_id}")
            
            # Connect to WebSocket using modern API
            ws_connection = await connect(ws_url) #type: ignore
            
            # Try somnia_watch first, fall back to eth_subscribe if not found
            subscribe_methods = ["somnia_watch", "eth_subscribe"]
            subscription_id = None
            last_error = None
            
            for method in subscribe_methods:
                try:
                    subscribe_request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": method,
                        "params": ["logs", subscription_params] if method == "eth_subscribe" else [subscription_params]
                    }
                    
                    await ws_connection.send(json.dumps(subscribe_request))
                    response = await ws_connection.recv()
                    response_data = json.loads(response)
                    
                    if "result" in response_data:
                        subscription_id = response_data["result"]
                        print(f"Subscribed using {method}: {subscription_id}")
                        break
                    elif "error" in response_data:
                        error = response_data["error"]
                        # If method not found, try next method
                        if error.get("code") == -32601:
                            last_error = error
                            continue
                        else:
                            raise ValueError(f"Subscription error: {error}")
                except Exception as e:
                    last_error = str(e)
                    continue
            
            if not subscription_id:
                await ws_connection.close()
                raise ValueError(
                    f"Failed to subscribe with any method. "
                    f"Tried: {', '.join(subscribe_methods)}. "
                    f"Last error: {last_error}. "
                    f"The WebSocket endpoint may not support subscriptions or requires different parameters."
                )
            
            # Store subscription info for callback handling
            subscription_info = {
                "subscriptionId": subscription_id,
                "connection": ws_connection,
                "unsubscribe": lambda: asyncio.create_task(self._unsubscribe(ws_connection, subscription_id)),
            }
            
            # Set up message listener if callbacks provided
            if init_params.on_data or init_params.on_error:
                async def listen_for_messages():
                    try:
                        async for message in ws_connection:
                            # Parse and handle the message
                            data = json.loads(message) if isinstance(message, str) else message
                            
                            # Check if this is a subscription notification
                            if isinstance(data, dict) and data.get("method") == "eth_subscription":
                                params = data.get("params", {})
                                if params.get("subscription") == subscription_id:
                                    if init_params.on_data:
                                        init_params.on_data(params.get("result"))
                    except Exception as e:
                        if init_params.on_error:
                            init_params.on_error(e)
                
                # Start listening in background
                asyncio.create_task(listen_for_messages())
            
            return subscription_info
            
        except Exception as e:
            print(f"subscribe error: {e}")
            traceback.print_exc()
        return None
    
    async def _unsubscribe(self, connection: Any, subscription_id: str) -> None:
        """
        Unsubscribe from a WebSocket subscription.
        
        Args:
            connection: WebSocket connection
            subscription_id: Subscription ID to unsubscribe
        """
        try:
            import json
            
            unsubscribe_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "eth_unsubscribe",
                "params": [subscription_id]
            }
            
            await connection.send(json.dumps(unsubscribe_request))
            await connection.close()
        except Exception as e:
            print(f"Unsubscribe error: {e}")
    
    async def deserialise_raw_data(
        self,
        raw_data: List[HexStr],
        schema_id: SchemaID,
    ) -> Union[List[HexStr], List[List[SchemaDecodedItem]], None]:
        """
        Deserialise raw data based on a public schema.
        
        Args:
            raw_data: Array of data to deserialise
            schema_id: Schema identifier for lookup
            
        Returns:
            Raw data if schema is private, decoded items or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            schema_lookup = await self._schema_lookup(
                contract_info["address"],
                contract_info["abi"],
                schema_id,
            )
            
            final_schema = schema_lookup.get("final_schema") if schema_lookup else None
            
            if final_schema:
                encoder = SchemaEncoder(final_schema)
                # Convert bytes to hex strings if needed
                hex_data = []
                for raw in raw_data:
                    if isinstance(raw, bytes):
                        hex_data.append(to_hex(raw))
                    else:
                        hex_data.append(raw)
                decoded_data = [encoder.decode_data(raw) for raw in hex_data]
                return decoded_data
            
            # Return raw data if no public schema (convert bytes to hex if needed)
            result = []
            for raw in raw_data:
                if isinstance(raw, bytes):
                    result.append(to_hex(raw))
                else:
                    result.append(raw)
            return result
        except Exception as e:
            print(f"deserialiseRawData error: {e}")
        return None
    
    async def get_schema_from_schema_id(
        self,
        schema_id: SchemaID,
    ) -> Union[Dict[str, Any], Exception, None]:
        """
        Request a schema given the schema id.
        
        Args:
            schema_id: The bytes32 unique identifier
            
        Returns:
            Schema info if public, Error or None
        """
        try:
            chain_id = await self.web3_client.get_chain_id()
            
            contract_info = await get_contract_address_and_abi(ContractRef(internal=KnownContracts.STREAMS, chain_id=chain_id))
            
            schema_lookup = await self._schema_lookup(
                contract_info["address"],
                contract_info["abi"],
                schema_id,
            )
            
            if not schema_lookup:
                raise ValueError(f"Unable to do schema lookup on [{schema_id}]")
            
            return schema_lookup
        except Exception as e:
            print(f"getSchemaFromSchemaId error: {e}")
            if isinstance(e, Exception):
                return e
        return None
    
    async def _schema_lookup(
        self,
        contract: ChecksumAddress,
        abi: List[Dict[str, Any]],
        schema_ref: SchemaReference,
    ) -> Optional[Dict[str, Any]]:
        """
        Internal schema lookup with parent schema resolution.
        
        Args:
            contract: Contract address
            abi: Contract ABI
            schema_ref: Schema reference (ID or literal schema)
            
        Returns:
            Schema info dictionary or None
        """
        # Validate input
        if not schema_ref or not schema_ref.strip():
            raise ValueError("Invalid schema or schema ID (zero data)")
        
        # Determine if we have a schema ID or literal schema
        schema_id: Optional[HexStr] = None
        lookup_schema_onchain = True
        
        if "0x" not in schema_ref.lower():
            # We have the literal schema, compute its ID
            schema_id = await self.compute_schema_id(schema_ref)
            if not schema_id:
                return None
            lookup_schema_onchain = False
        else:
            schema_id = HexStr(schema_ref)
        
        # Fetch schema and parent schema info from chain
        if lookup_schema_onchain:
            base_schema_lookup = await self.web3_client.read_contract(
                contract,
                abi,
                "schemaReverseLookup",
                [schema_id],
            )
        else:
            base_schema_lookup = schema_ref
        
        parent_schema_id = await self.web3_client.read_contract(
            contract,
            abi,
            "parentSchemaId",
            [schema_id],
        )
        
        # Lookup parent schema if exists
        parent_schema: Optional[str] = None
        if parent_schema_id != ZERO_BYTES32:
            parent_schema = await self.web3_client.read_contract(
                contract,
                abi,
                "schemaReverseLookup",
                [parent_schema_id],
            )
        
        # Compute final schema with parent
        final_schema = base_schema_lookup
        if parent_schema:
            final_schema = f"{final_schema}, {parent_schema}"
        
        if not final_schema:
            return None
        
        return {
            "base_schema": base_schema_lookup,
            "final_schema": final_schema,
            "schema_id": schema_id,
        }
