import asyncio
from eth_utils import to_hex, keccak
from eth_abi import encode
from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET, EventStream


async def main():
    sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"],
                               private_key="0x0000000000000000000000000000000000000000000000000000000000000001")

    event_signature = "TestV1(uint256 indexed x)"
    event_id = "TestV1"

    event_data = encode(
        ["uint256"],
        [13]
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

if __name__ == "__main__":
    asyncio.run(main())