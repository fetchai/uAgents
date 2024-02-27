import asyncio
import uuid
from time import time
from typing import Optional, Any, Type

import aiohttp

from uagents import Model
from uagents.crypto import Identity
from uagents.envelope import Envelope
from uagents.resolver import GlobalResolver, Resolver, RulesBasedResolver

from agent import Message


async def send_sync_message(
    destination: str,
    msg: Model,
    *,
    response: Type[Model],
    resolver: Optional[Resolver] = None,
) -> Optional[Any]:
    sender = Identity.generate()
    resolver = resolver or GlobalResolver()

    destination_address, endpoints = await resolver.resolve(destination)

    if len(endpoints) == 0:
        raise RuntimeError(
            f"Unable to resolve destination endpoint for address {destination}"
        )

    # Calculate when the envelope expires
    expires = int(time()) + 60

    # Handle external dispatch of messages
    env = Envelope(
        version=1,
        sender=sender.address,
        target=destination_address,
        session=uuid.uuid4(),
        schema_digest=Model.build_schema_digest(msg),
        protocol_digest=None,
        expires=expires,
    )
    env.encode_payload(msg.json())
    env.sign(sender)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoints[0],  # pick the first endpoint
            headers={
                "content-type": "application/json",
                "x-uagents-connection": "sync",
            },
            data=env.json(),
        ) as resp:
            resp.raise_for_status()

            # get the raw envelope content
            content = await resp.json()

            # parse the envelope and payload
            env = Envelope.parse_obj(content)
            payload = env.decode_payload()

            if response is None:
                return None

            return response.parse_raw(payload)


async def main():
    print("Hello from client")
    msg = Message(text="Hello there")
    destination_address = (
        "agent1qvur43kf2fcl8c4nudula7lrgthyhus0k27kusm344ujruyv62jlkccuxep"
    )

    resolver = RulesBasedResolver(
        {
            "agent1qvur43kf2fcl8c4nudula7lrgthyhus0k27kusm344ujruyv62jlkccuxep": "http://localhost:8000/submit"
        }
    )

    response = await send_sync_message(
        destination_address, msg, response=Message, resolver=resolver
    )

    print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
