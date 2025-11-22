import asyncio
from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET, DataSchemaRegistration


async def main():
    sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"],
                               private_key="0x0000000000000000000000000000000000000000000000000000000000000001")

    test_schema = "uint256 kills, address player"
    schema_id = await sdk.streams.compute_schema_id(test_schema)
    print(f"\nSchema ID for '{test_schema}' is {schema_id}")

    is_registered = await sdk.streams.is_data_schema_registered(schema_id)
    print(f"Is schema registered: {is_registered}")

    if not is_registered:
        registrations = [
            DataSchemaRegistration(
                schema_name="player_kill_count_v1",
                schema=test_schema,
                parent_schema_id=None
            )
        ]

        tx_hash = await sdk.streams.register_data_schemas(registrations)
        print(f"Schema registered! TX: 0x{tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())