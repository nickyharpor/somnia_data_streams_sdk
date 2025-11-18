import asyncio
from pprint import pprint
from web3 import Web3
from eth_typing import HexStr
from eth_utils import to_hex, keccak
from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET


async def main():
    sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"])

    schema_id = HexStr("0xa37520ea7ef3ebda07a325e952952f4364bc0266089b9da7fc63e7052a3602e8")
    publisher = Web3.to_checksum_address("0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf")

    print("Getting only the first data point...")
    data_at_index_zero = await sdk.streams.get_at_index(schema_id, publisher, 0)
    pprint(data_at_index_zero)

    print("=" * 69)

    print("Getting the first two data points...")
    all_data_between = await sdk.streams.get_between_range(schema_id, publisher, 0, 2)
    pprint(all_data_between)

    print("=" * 69)

    print("Getting the data point with data ID 'kills_1763211192'...")
    data_by_key = await sdk.streams.get_by_key(schema_id, publisher, to_hex(keccak(text="kills_1763211192")))
    pprint(data_by_key)

    print("=" * 69)

    print("Getting all data...")
    all_data = await sdk.streams.get_all_publisher_data_for_schema(schema_id, publisher)
    for i, data_items in enumerate(all_data):
        print(f"Data point {i + 1}:")
        for item in data_items:
            print(f"   {item.name}: {item.value.value}") # type: ignore


if __name__ == "__main__":
    asyncio.run(main())