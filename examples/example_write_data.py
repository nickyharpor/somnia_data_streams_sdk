import asyncio
import datetime
from eth_typing import HexStr
from eth_utils import to_hex, keccak
from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET, SchemaEncoder, SchemaItem, DataStream


async def main():
    sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"],
                               private_key="0x0000000000000000000000000000000000000000000000000000000000000001")

    plain_text_schema = "uint256 kills, address player"
    schema_id = HexStr("0xa37520ea7ef3ebda07a325e952952f4364bc0266089b9da7fc63e7052a3602e8")

    encoder = SchemaEncoder(plain_text_schema)
    encoded = encoder.encode_data([
        SchemaItem(name="kills", type="uint256", value=13),
        SchemaItem(name="player", type="address", value="0x7e5f4552091a69125d5dfcb7b8c2659029395bdf"),
    ])

    unix_timestamp = int(datetime.datetime.now().timestamp())
    data_id = to_hex(keccak(text=f"kills_{unix_timestamp}"))
    data_streams = [
        DataStream(
            id=data_id,
            schema_id=schema_id,
            data=encoded
        )
    ]

    tx_hash = await sdk.streams.set(data_streams)
    print(f"Data published! TX: 0x{tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())