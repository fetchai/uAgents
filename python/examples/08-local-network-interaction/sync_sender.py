import asyncio

from uagents import Model
from uagents.communication import send_sync_message

RECIPIENT_ADDRESS = (
    "test-agent://agent1q2kxet3vh0scsf0sm7y2erzz33cve6tv5uk63x64upw5g68kr0chkv7hw50"
)


class Message(Model):
    message: str


async def main():
    response = await send_sync_message(
        RECIPIENT_ADDRESS, Message(message="Hello there bob."), response_type=Message
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
