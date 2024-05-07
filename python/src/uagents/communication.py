# ruff: noqa: F821
"""Agent dispatch of exchange envelopes and synchronous messages."""

import asyncio
import logging
import uuid
from ast import Tuple
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Type, Union

import aiohttp
from pydantic import ValidationError
from uagents.config import DEFAULT_DISPENSER_INTERVAL, get_logger
from uagents.crypto import Identity
from uagents.dispatch import JsonStr, dispatcher
from uagents.envelope import Envelope
from uagents.models import Model
from uagents.resolver import GlobalResolver, Resolver

LOGGER = get_logger("dispenser", logging.DEBUG)


class DeliveryStatus(str, Enum):
    """Delivery status of a message."""

    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    QUEUED = "queued"


@dataclass
class MsgDigest:
    """
    Represents a message digest containing a message and its schema digest.

    Attributes:
        message (Any): The message content.
        schema_digest (str): The schema digest of the message.
    """

    message: Any
    schema_digest: str


@dataclass
class MsgStatus:
    """
    Represents the status of a sent message.

    Attributes:
        status (str): The delivery status of the message {'sent', 'delivered', 'failed'}.
        detail (str): The details of the message delivery.
        destination (str): The destination address of the message.
        endpoint (str): The endpoint the message was sent to.
    """

    status: DeliveryStatus
    detail: str
    destination: str
    endpoint: str


class Dispenser:
    """
    Dispenses messages externally.
    """

    def __init__(self):
        self._envelopes: List[Tuple[Envelope, bool]] = []
        self._timeout: float = DEFAULT_DISPENSER_INTERVAL
        self._resolver: Resolver = GlobalResolver()

    def configure(self, resolver: Resolver, timeout: Optional[float] = None):
        if resolver:
            self._resolver = resolver
        if timeout:
            self._timeout = timeout

    def add_envelope(self, envelope: Envelope, sync: bool = False):
        self._envelopes.append((envelope, sync))

    async def run(self):
        while True:
            for env, sync in self._envelopes:
                try:
                    await send_exchange_envelope(
                        envelope=env,
                        resolver=self._resolver,
                        sync=sync,
                    )  # how do we handle the MsgStatus response?
                    self._envelopes.remove((env, sync))
                except ValueError:
                    continue
            await asyncio.sleep(DEFAULT_DISPENSER_INTERVAL)


async def dispatch_local_message(
    sender: str,
    destination: str,
    schema_digest: str,
    message: JsonStr,
    session_id: uuid.UUID,
) -> MsgStatus:
    """Process a message locally."""
    await dispatcher.dispatch(
        sender=sender,
        destination=destination,
        schema_digest=schema_digest,
        message=message,
        session=session_id,
    )
    return MsgStatus(
        status=DeliveryStatus.DELIVERED,
        detail="Message dispatched locally",
        destination=destination,
        endpoint="",
    )


async def send_exchange_envelope(
    envelope: Envelope,
    resolver: Optional[Resolver] = None,
    sync: bool = False,
) -> Union[MsgStatus, Envelope]:
    if resolver is None:
        resolver = GlobalResolver()
    _, endpoints = await resolver.resolve(envelope.target)
    if len(endpoints) == 0:
        LOGGER.error(
            f"Unable to resolve destination endpoint for address {envelope.target}",
        )
        return MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Unable to resolve destination endpoint",
            destination=envelope.target,
            endpoint="",
        )
    headers = {"content-type": "application/json"}
    if sync:
        headers["x-uagents-connection"] = "sync"
    for endpoint in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers=headers,
                    data=envelope.json(),
                ) as resp:
                    success = resp.status == 200
                    if success:
                        if sync:
                            return await dispatch_sync_response_envelope(
                                Envelope.parse_obj(await resp.json())
                            )
                        return MsgStatus(
                            status=DeliveryStatus.DELIVERED,
                            detail="Message successfully delivered via HTTP",
                            destination=envelope.target,
                            endpoint=endpoint,
                        )
                LOGGER.warning(
                    f"Failed to send message to {envelope.target} @ {endpoint}: "
                    + (await resp.text()),
                )
        except aiohttp.ClientConnectorError as ex:
            LOGGER.warning(f"Failed to connect to {endpoint}: {ex}")
        except ValidationError as ex:
            LOGGER.warning(
                f"Sync message to {envelope.target} @ {endpoint} got invalid response: {ex}",
            )
        except Exception as ex:
            LOGGER.warning(
                f"Failed to send message to {envelope.target} @ {endpoint}: {ex}",
            )
    LOGGER.error(f"Failed to deliver message to {envelope.target}")
    return MsgStatus(
        status=DeliveryStatus.FAILED,
        detail="Message delivery failed",
        destination=envelope.target,
        endpoint="",
    )


# async def send_raw_exchange_envelope(
#     sender: AgentRepresentation,
#     destination: str,
#     resolver: Resolver,
#     schema_digest: str,
#     protocol_digest: Optional[str],
#     json_message: JsonStr,
#     logger: Optional[logging.Logger] = None,
#     timeout: int = 5,
#     session_id: Optional[uuid.UUID] = None,
#     sync: bool = False,
# ) -> Union[MsgStatus, Envelope]:
#     """
#     Standalone function to send a raw exchange envelope to an agent.

#     Args:
#         sender (AgentRepresentation): The representation of an agent.
#         destination (str): The destination address to send the message to.
#         resolver (Resolver): The resolver for address-to-endpoint resolution.
#         schema_digest (str): The schema digest of the message.
#         protocol_digest (Optional[str]): The protocol digest of the message.
#         json_message (JsonStr): The JSON-encoded message to be sent.
#         logger (Optional[logging.Logger]): The optional logger instance.
#         timeout (int): The timeout for sending the message, in seconds.
#         session_id (Optional[uuid.UUID]): The optional session ID.
#         sync (bool): Whether to send the message synchronously or asynchronously.

#     Returns:
#         Union[MsgStatus, Envelope]: The delivery status of the message, or in the case of a
#         successful synchronous message, the response envelope.
#     """
#     # Resolve the destination address and endpoint ('destination' can be a name or address)
#     destination_address, endpoints = await resolver.resolve(destination)
#     if len(endpoints) == 0:
#         log(
#             logger,
#             logging.ERROR,
#             f"Unable to resolve destination endpoint for address {destination}",
#         )

#         return MsgStatus(
#             status=DeliveryStatus.FAILED,
#             detail="Unable to resolve destination endpoint",
#             destination=destination,
#             endpoint="",
#         )

#     # Calculate when the envelope expires
#     expires = int(time()) + timeout

#     # Handle external dispatch of messages
#     env = Envelope(
#         version=1,
#         sender=sender.address,
#         target=destination_address,
#         session=session_id or uuid.uuid4(),
#         schema_digest=schema_digest,
#         protocol_digest=protocol_digest,
#         expires=expires,
#     )
#     env.encode_payload(json_message)
#     env.sign(sender.sign_digest)

#     dispenser.add_envelope(env)  # should happen in context of the agent


async def dispatch_sync_response_envelope(env: Envelope) -> MsgStatus:
    await dispatcher.dispatch(
        env.sender,
        env.target,
        env.schema_digest,
        env.decode_payload(),
        env.session,
    )
    return MsgStatus(
        status=DeliveryStatus.DELIVERED,
        detail="Sync message successfully delivered via HTTP",
        destination=env.target,
        endpoint="",
    )


async def send_sync_message(
    destination: str,
    message: Model,
    response_type: Type[Model] = None,
    sender: Identity = None,
    resolver: Resolver = None,
    timeout: int = 30,
) -> Union[Model, JsonStr, MsgStatus]:
    """
    Standalone function to send a synchronous message to an agent.

    Args:
        destination (str): The destination address to send the message to.
        message (Model): The message to be sent.
        response_type (Type[Model]): The optional type of the response message.
        sender (Identity): The optional sender identity (defaults to a generated identity).
        resolver (Resolver): The optional resolver for address-to-endpoint resolution.
        timeout (int): The optional timeout for the message response in seconds.

    Returns:
        Union[Model, JsonStr, MsgStatus]: On success, if the response type is provided, the response
        message is returned with that type. Otherwise, the JSON message is returned. On failure, a
        message status is returned.
    """
    response = await send_raw_exchange_envelope(
        sender or Identity.generate(),
        destination,
        resolver or GlobalResolver(),
        Model.build_schema_digest(message),
        protocol_digest=None,
        json_message=message.json(),
        timeout=timeout,
        sync=True,
    )
    if isinstance(response, Envelope):
        json_message = response.decode_payload()
        if response_type:
            return response_type.parse_raw(json_message)
        return json_message
    return response


dispenser = Dispenser()
