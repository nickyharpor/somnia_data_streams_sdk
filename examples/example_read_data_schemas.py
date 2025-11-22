import asyncio

from eth_typing import HexStr

from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET


async def main():
    sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"])

    print("Getting first 3 schemas...")
    schemas = await sdk.streams.get_all_schemas()
    for i, schema in enumerate(schemas[:3]):
        print(f"{i + 1}. {schema}")

    print("=" * 69)

    print("Getting schema ID for 'earthquake_event_v1'...")
    schema_bytes_from_id = await sdk.streams.schema_name_to_schema_id("earthquake_event_v1")
    schema_id = HexStr("0x" + schema_bytes_from_id.hex())
    print(schema_id)

    print("=" * 69)

    print(f"Getting schema by ID {schema_id}...")
    schema_by_id = await sdk.streams.get_schema_from_schema_id(schema_id)
    print(schema_by_id)

    print("=" * 69)

    id_from_schema_id = await sdk.streams.schema_id_to_schema_name(schema_id)
    print(id_from_schema_id)


if __name__ == "__main__":
    asyncio.run(main())