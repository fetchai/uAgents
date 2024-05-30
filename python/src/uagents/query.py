"""Query Envelopes."""

import uuid
from time import time
from typing import Optional

import aiohttp
from uagents.crypto import generate_user_address
from uagents.envelope import Envelope
from uagents.models import Model
from uagents.resolver import GlobalResolver, Resolver
from uagents.utils import get_logger

LOGGER = get_logger("query")


async def query(
    destination: str,
    message: Model,
    resolver: Optional[Resolver] = None,
    timeout: int = 30,
) -> Optional[Envelope]:
    """
    Query a remote agent with a message and retrieve the response envelope.

    Args:
        destination (str): The destination address of the remote agent.
        message (Model): The message to send.
        resolver (Optional[Resolver], optional): The resolver to use for endpoint resolution.
        Defaults to GlobalResolver.
        timeout (int): The timeout for the query in seconds. Defaults to 30.

    Returns:
        Optional[Envelope]: The response envelope if successful, otherwise None.
    """
    if resolver is None:
        resolver = GlobalResolver()

    # convert the message into object form
    json_message = message.json()
    schema_digest = Model.build_schema_digest(message)

    # resolve the endpoint
    destination_address, endpoints = await resolver.resolve(destination)
    if not endpoints or not destination_address:
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

    for endpoint in endpoints:
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    endpoints[0],
                    headers={
                        "content-type": "application/json",
                        "x-uagents-connection": "sync",
                    },
                    data=env.json(),
                    timeout=timeout,
                ) as response,
            ):
                success = response.status == 200

                if success:
                    return Envelope.parse_obj(await response.json())
        except aiohttp.ClientConnectorError as ex:
            LOGGER.warning(f"Failed to connect to {endpoint}: {ex}")
        except Exception as ex:
            LOGGER.warning(
                f"Failed to send sync message to {destination} @ {endpoint}: {ex}"
            )

    LOGGER.exception(f"Failed to send sync message to {destination}")
