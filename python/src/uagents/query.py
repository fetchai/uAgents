import uuid
from time import time
from typing import Optional

import aiohttp

from uagents.config import get_logger
from uagents.crypto import generate_user_address
from uagents.dispatch import JsonStr
from uagents.envelope import Envelope
from uagents.models import Model
from uagents.resolver import Resolver, GlobalResolver


LOGGER = get_logger("query")


async def query(
    destination: str,
    message: Model,
    resolver: Optional[Resolver] = None,
    timeout: Optional[int] = 30,
) -> Optional[Envelope]:
    if resolver is None:
        resolver = GlobalResolver()

    # convert the message into object form
    json_message = message.json()
    schema_digest = Model.build_schema_digest(message)

    # resolve the endpoint
    destination_address, endpoint = await resolver.resolve(destination)
    if endpoint is None:
        LOGGER.exception(
            f"Unable to resolve destination endpoint for address {destination}"
        )
        return

    # calculate when envelope expires
    expires = int(time()) + timeout

    # handle external dispatch of messages
    env = Envelope(
        version=1,
        sender=generate_user_address(),
        target=destination_address,
        session=uuid.uuid4(),
        schema_digest=schema_digest,
        expires=expires,
    )
    env.encode_payload(json_message)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoint,
            headers={
                "content-type": "application/json",
                "x-uagents-connection": "sync",
            },
            data=env.json(),
            timeout=timeout,
        ) as resp:
            success = resp.status == 200

            if success:
                return Envelope.parse_obj(await resp.json())

    LOGGER.exception(f"Unable to query {destination} @ {endpoint}")


def enclose_response(message: Model, sender: str, session: str) -> str:
    schema_digest = Model.build_schema_digest(message)
    return enclose_response_raw(message.json(), schema_digest, sender, session)


def enclose_response_raw(
    json_message: JsonStr, schema_digest: str, sender: str, session: str
) -> str:
    response_env = Envelope(
        version=1,
        sender=sender,
        target="",
        session=session,
        schema_digest=schema_digest,
    )
    response_env.encode_payload(json_message)
    return response_env.json()
