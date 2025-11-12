"""Tests for SchemaEncoder."""

import pytest
from eth_utils import to_hex
from somnia_streams import SchemaEncoder, SchemaItem


def test_schema_encoder_basic():
    """Test basic schema encoding/decoding."""
    schema = "uint256 value, address owner"
    encoder = SchemaEncoder(schema)
    
    # Use a properly checksummed address (Vitalik's address)
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    # Encode
    encoded = encoder.encode_data([
        SchemaItem(name="value", type="uint256", value=100),
        SchemaItem(name="owner", type="address", value=test_address),
    ])
    
    assert encoded.startswith("0x")
    
    # Decode
    decoded = encoder.decode_data(encoded)
    assert len(decoded) == 2
    assert decoded[0].name == "value"
    assert decoded[0].value.value == 100
    assert decoded[1].name == "owner"
    # Address should match (case-insensitive)
    assert decoded[1].value.value.lower() == test_address.lower()


def test_schema_encoder_bool():
    """Test boolean encoding."""
    schema = "bool active"
    encoder = SchemaEncoder(schema)
    
    encoded = encoder.encode_data([
        SchemaItem(name="active", type="bool", value=True),
    ])
    
    decoded = encoder.decode_data(encoded)
    assert decoded[0].value.value is True


def test_schema_encoder_string():
    """Test string encoding."""
    schema = "string message"
    encoder = SchemaEncoder(schema)
    
    encoded = encoder.encode_data([
        SchemaItem(name="message", type="string", value="Hello World"),
    ])
    
    decoded = encoder.decode_data(encoded)
    assert decoded[0].value.value == "Hello World"


def test_schema_encoder_bytes32():
    """Test bytes32 encoding."""
    from eth_utils import to_bytes
    
    schema = "bytes32 hash"
    encoder = SchemaEncoder(schema)
    
    # bytes32 needs to be bytes, not hex string
    test_hash = b'\xab' * 32
    encoded = encoder.encode_data([
        SchemaItem(name="hash", type="bytes32", value=test_hash),
    ])
    
    decoded = encoder.decode_data(encoded)
    # Decoded value will be hex string
    assert isinstance(decoded[0].value.value, str)
    assert decoded[0].value.value.startswith("0x")


def test_schema_encoder_array():
    """Test array encoding."""
    schema = "uint256[] values"
    encoder = SchemaEncoder(schema)
    
    encoded = encoder.encode_data([
        SchemaItem(name="values", type="uint256[]", value=[1, 2, 3, 4, 5]),
    ])
    
    decoded = encoder.decode_data(encoded)
    # eth_abi returns tuples for arrays
    assert list(decoded[0].value.value) == [1, 2, 3, 4, 5]


def test_schema_validation():
    """Test schema validation."""
    assert SchemaEncoder.is_schema_valid("uint256 value")
    assert SchemaEncoder.is_schema_valid("address owner, uint256 amount")
    assert SchemaEncoder.is_schema_valid("bool active, string name")


def test_invalid_param_count():
    """Test error on invalid parameter count."""
    schema = "uint256 value"
    encoder = SchemaEncoder(schema)
    
    with pytest.raises(ValueError, match="Invalid number of values"):
        encoder.encode_data([
            SchemaItem(name="value", type="uint256", value=100),
            SchemaItem(name="extra", type="uint256", value=200),
        ])


def test_invalid_param_type():
    """Test error on invalid parameter type."""
    schema = "uint256 value"
    encoder = SchemaEncoder(schema)
    
    with pytest.raises(ValueError, match="Incompatible param type"):
        encoder.encode_data([
            SchemaItem(name="value", type="address", value="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"),
        ])


def test_invalid_param_name():
    """Test error on invalid parameter name."""
    schema = "uint256 value"
    encoder = SchemaEncoder(schema)
    
    with pytest.raises(ValueError, match="Incompatible param name"):
        encoder.encode_data([
            SchemaItem(name="wrong", type="uint256", value=100),
        ])
