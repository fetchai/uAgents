"""Agent dispatch of exchange envelopes and synchronous messages."""

import asyncio
import logging
import uuid
from time import time
from typing import NoReturn

import aiohttp
from pydantic import UUID4, ValidationError
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity, is_user_address
from uagents_core.models import Model
from uagents_core.types import DeliveryStatus, MsgStatus

from uagents.config import DEFAULT_ENVELOPE_TIMEOUT_SECONDS
from uagents.dispatch import dispatcher
from uagents.resolver import GlobalResolver, Resolver
from uagents.types import (
    EnvelopeHistory,
    EnvelopeHistoryEntry,
    JsonStr,
)
from uagents.utils import get_logger

LOGGER: logging.Logger = get_logger("dispenser", logging.DEBUG)


class Dispenser:
    """Dispenses messages externally."""

    def __init__(self, msg_cache_ref: EnvelopeHistory | None = None):
        self._envelopes: asyncio.Queue[
            tuple[Envelope, list[str], asyncio.Future, bool]
        ] = asyncio.Queue()
        self._msg_cache_ref = msg_cache_ref

    def add_envelope(
        self,
        envelope: Envelope,
        endpoints: list[str],
        response_future: asyncio.Future,
        sync: bool = False,
    ) -> None:
        """
        Add an envelope to the dispenser.

        Args:
            envelope (Envelope): The envelope to send.
            endpoints (list[str]): The endpoints to send the envelope to.
            response_future (asyncio.Future): The future to set the response on.
            sync (bool): True if the message is synchronous. Defaults to False.
        """
        self._envelopes.put_nowait((envelope, endpoints, response_future, sync))

    async def run(self) -> NoReturn:
        """Run the dispenser routine."""
        while True:
            env, endpoints, response_future, sync = await self._envelopes.get()

            try:
                result: MsgStatus | Envelope = await send_exchange_envelope(
                    envelope=env,
                    endpoints=endpoints,
                    sync=sync,
                )
                response_future.set_result(result)

                if self._msg_cache_ref:
                    self._msg_cache_ref.add_entry(
                        EnvelopeHistoryEntry.from_envelope(env)
                    )
            except Exception as err:
                LOGGER.error(f"Failed to send envelope: {err}")


async def dispatch_local_message(
    sender: str,
    destination: str,
    schema_digest: str,
    message: JsonStr,
    session_id: uuid.UUID,
) -> MsgStatus:
    """Process a message locally."""
    await dispatcher.dispatch_msg(
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
    envelope: Envelope, endpoints: list[str], sync: bool = False
) -> MsgStatus | Envelope:
    """
    Method to send an exchange envelope.

    Args:
        envelope (Envelope): The envelope to send.
        endpoints (list[str]): The endpoints to send the envelope to.
        sync (bool): True if the message is synchronous. Defaults to False.

    Returns:
        MsgStatus | Envelope: Either the status of the message or the response envelope.
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
                            env = Envelope.model_validate(await resp.json())
                            if env.signature:
                                verified = False
                                try:
                                    verified = env.verify()
                                except Exception as ex:
                                    errors.append(
                                        f"Received response envelope that failed verification: {ex}"
                                    )
                                if not verified:
                                    continue
                            return await dispatch_sync_response_envelope(env, endpoint)
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


async def dispatch_sync_response_envelope(
    env: Envelope, endpoint: str
) -> MsgStatus | Envelope:
    """Dispatch a synchronous response envelope locally."""
    # if the sender is awaiting a response, dispatch the message back to the sending function
    if dispatcher.dispatch_pending_response(
        sender=env.sender,
        destination=env.target,
        session=env.session,
        message=env.decode_payload(),
    ):
        return MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Sync message successfully delivered via HTTP",
            destination=env.sender,
            endpoint=endpoint,
            session=env.session,
        )
    # Otherwise return the envelope (most likely the response to a standalone sending function)
    return env


async def send_message_raw(
    destination: str,
    message_schema_digest: str,
    message_body: JsonStr,
    response_type: type[Model] | None = None,
    sender: Identity | str | None = None,
    resolver: Resolver | None = None,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    sync: bool = False,
) -> Model | JsonStr | MsgStatus | Envelope:
    """
    Standalone function to send a message to an agent.

    Args:
        destination (str): The destination address to send the message to.
        message_schema_digest (str): The schema digest of the message.
        message_body (JsonStr): The JSON-formatted message to be sent.
        response_type (type[Model] | None): The optional type of the response message.
        sender (Identity | str | None): The optional sender identity or user address.
        resolver (Resolver | None): The optional resolver for address-to-endpoint resolution.
        timeout (int): The timeout for the message response in seconds. Defaults to 30.
        sync (bool): True if the message is synchronous.

    Returns:
        Model | JsonStr | MsgStatus | Envelope: On success, if the response type is provided,
        the response message is returned with that type. Otherwise, the JSON message is returned.
        If the sender is a user address, the response envelope is returned.
        On failure, a message status is returned.
    """
    sender_address = None
    if isinstance(sender, str) and is_user_address(sender):
        sender_address = sender
    if sender is None:
        sender = Identity.generate()
    if isinstance(sender, Identity):
        sender_address = sender.address
    if not sender_address:
        raise ValueError("Invalid sender address")

    if resolver is None:
        resolver = GlobalResolver()

    destination_address, endpoints = await resolver.resolve(destination)
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
        sender=sender_address,
        target=destination_address,
        session=uuid.uuid4(),
        schema_digest=message_schema_digest,
        expires=int(time()) + timeout,
    )
    env.encode_payload(message_body)
    if not is_user_address(sender_address) and isinstance(sender, Identity):
        env.sign(sender)

    response = await send_exchange_envelope(
        envelope=env,
        endpoints=endpoints,
        sync=sync,
    )
    if isinstance(response, Envelope):
        if env.signature is None:
            return response
        json_message = response.decode_payload()
        if response_type:
            return response_type.model_validate_json(json_message)
        return json_message
    return response


async def send_message(
    destination: str,
    message: Model,
    response_type: type[Model] | None = None,
    sender: Identity | str | None = None,
    resolver: Resolver | None = None,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    sync: bool = False,
) -> Model | JsonStr | MsgStatus | Envelope:
    """
    Standalone function to send a message to an agent.

    Args:
        destination (str): The destination address to send the message to.
        message (Model): The message to be sent.
        response_type (type[Model] | None): The optional type of the response message.
        sender (Identity | str | None): The optional sender identity or user address.
        resolver (Resolver | None): The optional resolver for address-to-endpoint resolution.
        timeout (int): The timeout for the message response in seconds. Defaults to 30.
        sync (bool): True if the message is synchronous.

    Returns:
        Model | JsonStr | MsgStatus | Envelope: On success, if the response type is provided,
        the response message is returned with that type. Otherwise, the JSON message is returned.
        If the sender is a user address, the response envelope is returned.
        On failure, a message status is returned.
    """
    return await send_message_raw(
        destination=destination,
        message_schema_digest=Model.build_schema_digest(message),
        message_body=message.model_dump_json(),
        response_type=response_type,
        sender=sender,
        resolver=resolver,
        timeout=timeout,
        sync=sync,
    )


async def send_sync_message(
    destination: str,
    message: Model,
    response_type: type[Model] | None = None,
    sender: Identity | str | None = None,
    resolver: Resolver | None = None,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
) -> Model | JsonStr | MsgStatus | Envelope:
    """
    Standalone function to send a synchronous message to an agent.

    Args:
        destination (str): The destination address to send the message to.
        message (Model): The message to be sent.
        response_type (type[Model] | None): The optional type of the response message.
        sender (Identity | str | None): The optional sender identity or user address.
        resolver (Resolver | None): The optional resolver for address-to-endpoint resolution.
        timeout (int): The timeout for the message response in seconds. Defaults to 30.
        sync (bool): True if the message is synchronous.

    Returns:
        Model | JsonStr | MsgStatus | Envelope: On success, if the response type is provided,
        the response message is returned with that type. Otherwise, the JSON message is returned.
        If the sender is a user address, the response envelope is returned.
        On failure, a message status is returned.
    """
    return await send_message(
        destination=destination,
        message=message,
        response_type=response_type,
        sender=sender,
        resolver=resolver,
        timeout=timeout,
        sync=True,
    )


def enclose_response(
    message: Model, sender: str, session: UUID4, target: str = ""
) -> JsonStr:
    """
    Enclose a response message within an envelope.

    Args:
        message (Model): The response message to enclose.
        sender (str): The sender's address.
        session (str): The session identifier.
        target (str): The target address.

    Returns:
        str: The JSON representation of the response envelope.
    """
    schema_digest = Model.build_schema_digest(message)
    return enclose_response_raw(
        json_message=message.model_dump_json(),
        schema_digest=schema_digest,
        sender=sender,
        session=session,
        target=target,
    )


def enclose_response_raw(
    json_message: JsonStr,
    schema_digest: str,
    sender: str,
    session: UUID4,
    target: str = "",
) -> JsonStr:
    """
    Enclose a raw response message within an envelope.

    Args:
        json_message (JsonStr): The JSON-formatted response message to enclose.
        schema_digest (str): The schema digest of the message.
        sender (str): The sender's address.
        session (UUID4): The session identifier.
        target (str): The target address.

    Returns:
        str: The JSON representation of the response envelope.
    """
    response_env = Envelope(
        version=1,
        sender=sender,
        target=target,
        session=session,
        schema_digest=schema_digest,
    )
    response_env.encode_payload(json_message)
    return response_env.model_dump_json()
