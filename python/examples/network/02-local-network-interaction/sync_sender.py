import asyncio

from uagents import Model
from uagents.communication import send_sync_message

RECIPIENT_ADDRESS = "put_RECIPIENT_ADDRESS_here"


class Message(Model):
    message: str


async def main():
    response = await send_sync_message(
        RECIPIENT_ADDRESS, Message(message="Hello there bob."), response_type=Message
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
