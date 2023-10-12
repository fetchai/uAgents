"""Query Envelopes."""

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
    """
    Query a remote agent with a message and retrieve the response envelope.

    Args:
        destination (str): The destination address of the remote agent.
        message (Model): The message to send.
        resolver (Optional[Resolver], optional): The resolver to use for endpoint resolution.
        Defaults to GlobalResolver.
        timeout (Optional[int], optional): The timeout for the query in seconds. Defaults to 30.

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
    if len(endpoints) == 0:
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
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoints[0],
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
        except aiohttp.ClientConnectorError as ex:
            LOGGER.warning(f"Failed to connect to {endpoint}: {ex}")
        except Exception as ex:
            LOGGER.warning(
                f"Failed to send sync message to {destination} @ {endpoint}: {ex}"
            )

    LOGGER.exception(f"Failed to send sync message to {destination}")


def enclose_response(message: Model, sender: str, session: str) -> str:
    """
    Enclose a response message within an envelope.

    Args:
        message (Model): The response message to enclose.
        sender (str): The sender's address.
        session (str): The session identifier.

    Returns:
        str: The JSON representation of the response envelope.
    """
    schema_digest = Model.build_schema_digest(message)
    return enclose_response_raw(message.json(), schema_digest, sender, session)


def enclose_response_raw(
    json_message: JsonStr, schema_digest: str, sender: str, session: str
) -> str:
    """
    Enclose a raw response message within an envelope.

    Args:
        json_message (JsonStr): The JSON-formatted response message to enclose.
        schema_digest (str): The schema digest of the message.
        sender (str): The sender's address.
        session (str): The session identifier.

    Returns:
        str: The JSON representation of the response envelope.
    """
    response_env = Envelope(
        version=1,
        sender=sender,
        target="",
        session=session,
        schema_digest=schema_digest,
    )
    response_env.encode_payload(json_message)
    return response_env.json()
