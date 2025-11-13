# Somnia Data Streams Python SDK

The Somnia Data Streams Python SDK enables streaming data on-chain, integrated with off-chain reactivity to unlock new paradigms in the blockchain ecosystem.


## Features

- Easy and intuitive interface and flow
- Consistent with Somnia Data Streams JS/TS SDK
- Schema encoding and decoding for structured data
- Type-safe API with comprehensive type definitions
- Asynchronized architecture for better CPU utilization on high load
- Extensive unit tests and integration tests


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
    SchemaItem(name="owner", type="address", value="0x7e5f4552091a69125d5dfcb7b8c2659029395bdf"),
])
print(f"Encoded Schema: {encoded}")

decoded = encoder.decode_data(encoded)
print("Decoded Schema:")
for item in decoded:
    print(f"  {item.name} ({item.type}): {item.value.value}")
```

### Register a Schema (Consumes Gas)

```python
from somnia_data_streams_sdk import DataSchemaRegistration

registrations = [
    DataSchemaRegistration(
        id="your-unique-id-here-otherwise-wont-register",
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

### Publish Data

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

If it's a new feature, don't forget to write unit tests and integration tests for it.