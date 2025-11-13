import pytest
import os
from web3 import Web3
from eth_account import Account

from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

@pytest.fixture
def test_account():
    """Create a test account with a known private key."""
    # This is a well-known test private key (DO NOT use in production)
    private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    return Account.from_key(private_key)


@pytest.mark.asyncio
async def test_get_all_schemas():
    # Read-only access (no private key needed)
    sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"])

    schemas = await sdk.streams.get_all_schemas()
    #for i, schema in enumerate(schemas):
    #    print(f"{i + 1}. {schema}")
    
    # Verify
    assert schemas is not None
    assert isinstance(schemas, list)

