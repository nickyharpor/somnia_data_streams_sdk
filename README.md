# Somnia Data Streams Python SDK

The Somnia Data Streams Python SDK enables streaming data on-chain, integrated with off-chain reactivity to unlock new paradigms in the blockchain ecosystem.

[![PyPI Version](https://img.shields.io/pypi/v/somnia-data-streams-sdk.svg)](https://pypi.org/project/somnia-data-streams-sdk/)


## Features

- Easy and intuitive interface and flow
- Consistent with Somnia Data Streams JS/TS SDK
- Schema encoding and decoding for structured data
- Type-safe API with comprehensive type definitions
- Asynchronized architecture for better CPU utilization on high load
- Extensive unit tests and integration tests
- Example code snippets for all functionalities


## Installation

```bash
pip install somnia-data-streams-sdk
```


## Quick Start

### Initialize the SDK

```python
from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET

# Read-only access (no private key needed)
sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"])

# With write access (provide private key for transaction signing)
sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"], private_key="0x...")
```

### Get All Registered Schemas

```python
import asyncio

schemas = await sdk.streams.get_all_schemas()
for i, schema in enumerate(schemas):
    print(f"{i+1}. {schema}")
```

### Compute Schema ID

```python
test_schema = "uint256 balance, address owner"
schema_id = await sdk.streams.compute_schema_id(test_schema)
print(f"\nSchema ID for '{test_schema}': {schema_id}")
```

### Check if Schema is Registered

```python
is_registered = await sdk.streams.is_data_schema_registered(schema_id)
print(f"Schema registered: {is_registered}")
```

### Schema Encoding/Decoding

```python
from somnia_data_streams_sdk import SchemaEncoder, SchemaItem

encoder = SchemaEncoder("uint256 balance, address owner")
encoded = encoder.encode_data([
    SchemaItem(name="balance", type="uint256", value=666),
    SchemaItem(name="owner", type="address", value="0x..."),
])
print(f"Encoded Schema: {encoded}")

decoded = encoder.decode_data(encoded)
print("Decoded Schema:")
for item in decoded:
    print(f"  {item.name} ({item.type}): {item.value.value}")
```

### Register a Data Schema (Consumes Gas)

```python
from somnia_data_streams_sdk import DataSchemaRegistration

registrations = [
    DataSchemaRegistration(
        schema_name="your-unique-id-here-otherwise-wont-register",
        schema=test_schema,
        parent_schema_id=None
    )
]
tx_hash = await sdk.streams.register_data_schemas(registrations)
if tx_hash and isinstance(tx_hash, str) and tx_hash.startswith("0x"):
    print(f"Schema registered! TX: {tx_hash}")
else:
    print("Schema already registered or registration error")
```

### Publish Data (Consumes Gas)

```python
from eth_utils import to_hex, keccak
from somnia_data_streams_sdk import DataStream

data_id = to_hex(keccak(text="your-unique-id-here-for-this-data"))
data_streams = [
    DataStream(
        id=data_id,
        schema_id=schema_id,
        data=encoded,
    )
]
tx_hash = await sdk.streams.set(data_streams)
if tx_hash:
    print(f"Data published! TX: {tx_hash}")
else:
    print("Data publishing failed")
```

### Read Data

```python
data = await sdk.streams.get_all_publisher_data_for_schema(
    schema_id=schema_id,
    publisher=sdk.streams.web3_client.client.account.address,
)
    
if data:
    print(f"Found {len(data)} data points")
    if isinstance(data[0], list):  # Decoded data
        for i, decoded_items in enumerate(data):
            print(f"\nData point {i+1}:")
            for item in decoded_items:
                print(f"  {item.name}: {item.value.value}")
    else:  # Raw data
        print("Raw data (schema not public):", data)
```

### Register Events (Consumes Gas)

```python
from somnia_data_streams_sdk import EventSchema, EventParameter
from eth_utils import to_hex, keccak

event_signature = "TestV1(uint256 indexed x)"
event_id = "TestV1"

event_schemas = [
    EventSchema(
        params=[
            EventParameter(name="x", param_type="uint256", is_indexed=True)
        ],
        event_topic=to_hex(keccak(text=event_signature))
    )
]

tx_hash = await sdk.streams.register_event_schemas(
    ids=[event_id],
    schemas=event_schemas
)

if tx_hash and isinstance(tx_hash, str):
    print(f"Event schema registered! TX: 0x{tx_hash}")
else:
    print("Event schema registration failed or already registered")

time.sleep(5) # gives Somnia's blockchain a short time to register the event

tx_hash = await sdk.streams.manage_event_emitters_for_registered_streams_event(
    event_id, "0x...", True) # Replace 0x... with your public key
print(f"Event permission added! TX: 0x{tx_hash}")
```

### Emit Events (Consumes Gas)

```python
from eth_abi import encode
from somnia_data_streams_sdk import EventStream

event_data = encode(
    ["uint256"],
    [13] # Replace 13 with any unsigned int value you want to emit
)

events = [
    EventStream(
        id=event_id,
        argument_topics=[to_hex(keccak(text=event_signature))],
        data=event_data
    )
]

tx_hash = await sdk.streams.emit_events(events)
if tx_hash and isinstance(tx_hash, str):
    print(f"Events emitted! TX: 0x{tx_hash}")
else:
    print("Event emission failed")
```

### Subscribe to Events

```python
from somnia_data_streams_sdk import SubscriptionInitParams

def on_data(data):
    print(data)

def on_error(error):
    print(error)

subscription = await sdk.streams.subscribe(
    SubscriptionInitParams(
        somnia_streams_event_id="TestV1",
        eth_calls=[],
        on_data=on_data,
        on_error=on_error,
        only_push_changes=True
    )
)

print("Subscribed to TestV1. Press Ctrl+C to stop.")

try:
    await asyncio.Future()
except:
    await subscription.get("unsubscribe")
```


## API Reference

### Main Classes

- `SDK` - Main SDK class for interacting with Somnia Data Streams
- `SchemaEncoder` - Encode and decode data schemas

### Chain Configuration

- `SOMNIA_TESTNET` - Testnet configuration (Chain ID: 50312)
- `SOMNIA_MAINNET` - Mainnet configuration (Chain ID: 5031)
- `get_chain_config(chain_id)` - Get chain configuration by ID
- `get_default_rpc_url(chain_id)` - Get default RPC URL for a chain

### Frequently Used Types

- `SubscriptionInitParams`
- `SchemaItem`, `SchemaDecodedItem`
- `EventParameter`, `EventSchema`, `EventStream`
- `DataStream`, `DataSchemaRegistration`


## Contribution Guide

If it's bug fix or code improvement (i.e. not a new feature), please make sure your code passes all tests before submitting a PR.

```bash
pytest -v -s
```

If it's a new feature, don't forget to write examples, unit tests, and integration tests for it.