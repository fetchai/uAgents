import logging
import uuid
from typing import Optional

import aiohttp

from nexus.crypto import generate_query_user
from nexus.envelope import Envelope
from nexus.models import Model
from nexus.resolver import Resolver, AlmanacResolver


async def query(
    destination: str, message: Model, resolver: Optional[Resolver] = None
) -> Optional[Envelope]:
    if resolver is None:
        resolver = AlmanacResolver()

    # convert the message into object form
    json_message = message.json()
    schema_digest = Model.build_schema_digest(message)

    # resolve the endpoint
    endpoint = await resolver.resolve(destination)
    if endpoint is None:
        logging.exception(
            f"Unable to resolve destination endpoint for address {destination}"
        )
        return

    # handle external dispatch of messages
    env = Envelope(
        version=1,
        sender=generate_query_user(),
        target=destination,
        session=uuid.uuid4(),
        protocol=schema_digest,
    )
    env.encode_payload(json_message)

    success = False
    async with aiohttp.ClientSession() as session:
        async with session.post(
            endpoint,
            headers={
                "content-type": "application/json",
                "uagents-query": "",
            },
            data=env.json(),
        ) as resp:
            success = resp.status == 200

            if success:
                return Envelope.parse_obj(await resp.json())

    logging.exception(f"Unable to query {destination} @ {endpoint}")


def enclose_response(message: Model, sender: str, session: str) -> dict:
    response_env = Envelope(
        version=1,
        sender=sender,
        target="",
        session=session,
        protocol=Model.build_schema_digest(message),
    )
    response_env.encode_payload(message.json())
    return response_env.json()
