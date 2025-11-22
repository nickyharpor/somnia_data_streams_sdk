import asyncio
import traceback
from pprint import pprint
from somnia_data_streams_sdk import SDK, SOMNIA_TESTNET, SubscriptionInitParams


def on_data(data):
    print("Full event data:")
    pprint(data)
    print("Decoded event data value:")
    print(int(data.get("result").get("data").hex(), 16))

    
def on_error(error):
    print(f"Subscription error: {error}")


async def main():
    sdk = SDK.create_for_chain(SOMNIA_TESTNET["id"],
                               private_key="0x0000000000000000000000000000000000000000000000000000000000000001")

    try:
        subscription = await sdk.streams.subscribe(
            SubscriptionInitParams(
                somnia_streams_event_id="TestV1",
                eth_calls=[],
                on_data=on_data,
                on_error=on_error,
                only_push_changes=True,
                context=None  # Optional context for filtering
            )
        )
        
        if subscription:
            print(f"Subscription ID: {subscription.get('subscriptionId')}")
            print("Run example_emit_events.py to emit a new TestV1 event")
            print("Waiting for events... (Press Ctrl+C to stop)")

            await asyncio.sleep(60)  # Listen for 60 seconds
            
            print("Unsubscribing...")
            unsubscribe_fn = subscription.get("unsubscribe")
            if unsubscribe_fn:
                await unsubscribe_fn()
                print("Unsubscribed successfully!")
        else:
            print("Failed to subscribe")
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
