"""Agent dispatch of exchange envelopes and synchronous messages."""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from time import time
from typing import Any, List, Optional, Tuple, Type, Union

import aiohttp
from pydantic import ValidationError
from uagents.crypto import Identity
from uagents.dispatch import JsonStr, dispatcher
from uagents.envelope import Envelope
from uagents.models import Model
from uagents.resolver import GlobalResolver, Resolver, parse_identifier
from uagents.utils import get_logger

LOGGER = get_logger("dispenser", logging.DEBUG)


class DeliveryStatus(str, Enum):
    """Delivery status of a message."""

    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


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
        session (Optional[uuid.UUID]): The session ID of the message.
    """

    status: DeliveryStatus
    detail: str
    destination: str
    endpoint: str
    session: Optional[uuid.UUID] = None


class Dispenser:
    """
    Dispenses messages externally.
    """

    def __init__(self):
        self._envelopes: List[Tuple[Envelope, List[str], asyncio.Future, bool]] = []

    def add_envelope(
        self,
        envelope: Envelope,
        endpoints: List[str],
        response_future: asyncio.Future,
        sync: bool = False,
    ):
        """
        Add an envelope to the dispenser.

        Args:
            envelope (Envelope): The envelope to send.
            endpoints (List[str]): The endpoints to send the envelope to.
            response_future (asyncio.Future): The future to set the response on.
            sync (bool, optional): True if the message is synchronous. Defaults to False.
        """
        self._envelopes.append((envelope, endpoints, response_future, sync))

    async def run(self):
        """Run the dispenser routine."""
        while True:
            for env, endpoints, response_future, sync in self._envelopes:
                try:
                    result = await send_exchange_envelope(
                        envelope=env,
                        endpoints=endpoints,
                        sync=sync,
                    )
                    response_future.set_result(result)
                except Exception as err:
                    LOGGER.error(f"Failed to send envelope: {err}")
                finally:  # sending an envelope is only tried once
                    self._envelopes.remove((env, endpoints, response_future, sync))
            await asyncio.sleep(0)


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
        session=session_id,
    )


async def send_exchange_envelope(
    envelope: Envelope,
    endpoints: List[str],
    sync: bool = False,
) -> Union[MsgStatus, Envelope]:
    """
    Method to send an exchange envelope.

    Args:
        envelope (Envelope): The envelope to send.
        resolver (Optional[Resolver], optional): The resolver to use. Defaults to None.
        sync (bool, optional): True if the message is synchronous. Defaults to False.

    Returns:
        Union[MsgStatus, Envelope]: Either the status of the message or the response envelope.
    """
    headers = {"content-type": "application/json"}
    if sync:
        headers["x-uagents-connection"] = "sync"
    errors = []
    for endpoint in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers=headers,
                    data=envelope.model_dump_json(),
                ) as resp:
                    success = resp.status == 200
                    if success:
                        if sync:
                            return await dispatch_sync_response_envelope(
                                Envelope.model_validate(await resp.json())
                            )
                        return MsgStatus(
                            status=DeliveryStatus.DELIVERED,
                            detail="Message successfully delivered via HTTP",
                            destination=envelope.target,
                            endpoint=endpoint,
                            session=envelope.session,
                        )
                errors.append(await resp.text())
        except aiohttp.ClientConnectorError as ex:
            errors.append(f"Failed to connect: {ex}")
        except ValidationError as ex:
            errors.append(f"Invalid sync response: {ex}")
        except Exception as ex:
            errors.append(f"Failed to send message: {ex}")
    LOGGER.error(
        f"Failed to deliver message to {envelope.target} @ {endpoints}: " + str(errors)
    )
    return MsgStatus(
        status=DeliveryStatus.FAILED,
        detail="Message delivery failed",
        destination=envelope.target,
        endpoint="",
        session=envelope.session,
    )


async def dispatch_sync_response_envelope(env: Envelope) -> Union[MsgStatus, Envelope]:
    """Dispatch a synchronous response envelope locally."""
    # If there are no sinks registered, return the envelope back to the caller
    if len(dispatcher.sinks) == 0:
        return env
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
        session=env.session,
    )


async def send_sync_message(
    destination: str,
    message: Model,
    response_type: Optional[Type[Model]] = None,
    sender: Optional[Identity] = None,
    resolver: Optional[Resolver] = None,
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
    if sender is None:
        sender = Identity.generate()
    if resolver is None:
        resolver = GlobalResolver()

    _, _, parsed_address = parse_identifier(destination)

    destination_address, endpoints = await resolver.resolve(parsed_address)
    if not endpoints or not destination_address:
        return MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Failed to resolve destination address",
            destination=destination,
            endpoint="",
            session=None,
        )

    env = Envelope(
        version=1,
        sender=sender.address,
        target=destination_address,
        session=uuid.uuid4(),
        schema_digest=Model.build_schema_digest(message),
        expires=int(time()) + timeout,
    )
    env.encode_payload(message.model_dump_json())
    env.sign(sender.sign_digest)

    response = await send_exchange_envelope(
        envelope=env,
        endpoints=endpoints,
        sync=True,
    )
    if isinstance(response, Envelope):
        json_message = response.decode_payload()
        if response_type:
            return response_type.model_validate_json(json_message)
        return json_message
    return response
