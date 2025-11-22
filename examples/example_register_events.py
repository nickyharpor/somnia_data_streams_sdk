import asyncio
from eth_utils import to_hex, keccak
import time
from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET, EventSchema, EventParameter


async def main():
    sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"],
                               private_key="0x0000000000000000000000000000000000000000000000000000000000000001")

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
    
    time.sleep(5)

    tx_hash = await sdk.streams.manage_event_emitters_for_registered_streams_event(
        event_id, "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf", True)
    print(f"Event permission added! TX: 0x{tx_hash}")

if __name__ == "__main__":
    asyncio.run(main())