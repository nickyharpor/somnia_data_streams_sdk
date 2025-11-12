"""Tests for validation utilities."""

import pytest
from somnia_streams.utils import assert_address_is_valid, is_valid_hex


def test_valid_address():
    """Test valid address validation."""
    # Use a properly checksummed address (Vitalik's address)
    valid_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    assert_address_is_valid(valid_address)  # Should not raise


def test_invalid_address():
    """Test invalid address validation."""
    invalid_address = "not-an-address"
    
    with pytest.raises(ValueError, match="Invalid address"):
        assert_address_is_valid(invalid_address)


def test_zero_address():
    """Test zero address validation."""
    zero_address = "0x0000000000000000000000000000000000000000"
    
    with pytest.raises(ValueError, match="Zero address"):
        assert_address_is_valid(zero_address)


def test_zero_address_allowed():
    """Test zero address when explicitly allowed."""
    zero_address = "0x0000000000000000000000000000000000000000"
    assert_address_is_valid(zero_address, disable_zero_address_check=True)


def test_is_valid_hex():
    """Test hex string validation."""
    assert is_valid_hex("0x1234")
    assert is_valid_hex("0xabcdef")
    assert is_valid_hex("1234")
    assert is_valid_hex("ABCDEF")
    
    assert not is_valid_hex("0xGHIJ")
    assert not is_valid_hex("not-hex")
    assert not is_valid_hex("")
