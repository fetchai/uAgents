"""Agent Context and Message Handling"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from time import time
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

import aiohttp
import requests
from cosmpy.aerial.client import LedgerClient
from pydantic import ValidationError
from uagents.config import (
    ALMANAC_API_URL,
    DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    DEFAULT_SEARCH_LIMIT,
    TESTNET_PREFIX,
)
from uagents.crypto import Identity
from uagents.dispatch import JsonStr, dispatcher
from uagents.envelope import Envelope
from uagents.models import ErrorMessage, Model
from uagents.resolver import GlobalResolver, Resolver, parse_identifier
from uagents.storage import KeyValueStore

if TYPE_CHECKING:
    from uagents.protocol import Protocol

IntervalCallback = Callable[["Context"], Awaitable[None]]
MessageCallback = Callable[["Context", str, Any], Awaitable[None]]
EventCallback = Callable[["Context"], Awaitable[None]]
WalletMessageCallback = Callable[["Context", Any], Awaitable[None]]


ERROR_MESSAGE_DIGEST = Model.build_schema_digest(ErrorMessage)


def log(logger: Optional[logging.Logger], level: str, message: str):
    if logger:
        logger.log(level, message)


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
    """

    status: DeliveryStatus
    detail: str
    destination: str
    endpoint: str


class AgentRepresentation:
    """
    Represents an agent in the context of a message.

    Attributes:
        _address (str): The address of the agent.
        _name (Optional[str]): The name of the agent.
        _signing_callback (Callable): The callback for signing messages.

    Properties:
        name (str): The name of the agent.
        address (str): The address of the agent.
        identifier (str): The agent's address and network prefix.

    Methods:
        sign_digest(data: bytes) -> str: Sign the provided data with the agent's identity.
    """

    def __init__(
        self,
        address: str,
        name: Optional[str],
        signing_callback: Callable,
    ):
        """
        Initialize the AgentRepresentation instance.

        Args:
            address (str): The address of the context.
            name (Optional[str]): The optional name associated with the context.
            signing_callback (Callable): The callback for signing messages.
        """
        self._address = address
        self._name = name
        self._signing_callback = signing_callback

    @property
    def name(self) -> str:
        """
        Get the name associated with the context or a truncated address if name is None.

        Returns:
            str: The name or truncated address.
        """
        if self._name is not None:
            return self._name
        return self._address[:10]

    @property
    def address(self) -> str:
        """
        Get the address of the context.

        Returns:
            str: The address of the context.
        """
        return self._address

    @property
    def identifier(self) -> str:
        """
        Get the address of the agent used for communication including the network prefix.

        Returns:
            str: The agent's address and network prefix.
        """
        return TESTNET_PREFIX + "://" + self._address

    def sign_digest(self, data: bytes) -> str:
        """
        Sign the provided data with the callback of the agent's identity.

        Args:
            data (bytes): The data to sign.

        Returns:
            str: The signature of the data.
        """
        return self._signing_callback(data)


class InternalContext:
    """
    Represents the agent internal context for proactive behaviour.

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """

    def __init__(
        self,
        agent: AgentRepresentation,
        storage: KeyValueStore,
        resolve: Resolver,  # may be outsourced
        ledger: LedgerClient,
        interval_messages: Optional[Set[str]] = None,
        wallet_messaging_client: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.agent = agent
        self.storage = storage
        self._resolver = resolve
        self.ledger = ledger
        self._session = None
        self._interval_messages = interval_messages
        self._wallet_messaging_client = wallet_messaging_client
        self._logger = logger
        self._outbound_messages: Dict[str, Tuple[JsonStr, str]] = {}

    @property
    def logger(self) -> logging.Logger:
        """
        Get the logger instance associated with the context.

        Returns:
            logging.Logger: The logger instance.
        """
        return self._logger

    @property
    def session(self) -> uuid.UUID:
        """
        Get the session UUID associated with the context.

        Returns:
            uuid.UUID: The session UUID.
        """
        return self._session

    @property
    def outbound_messages(self) -> Dict[str, Tuple[JsonStr, str]]:
        """
        Get the dictionary of outbound messages associated with the context.

        Returns:
            Dict[str, Tuple[JsonStr, str]]: The dictionary of outbound messages.
        """
        return self._outbound_messages

    @staticmethod
    def get_agents_by_protocol(
        protocol_digest: str,
        limit: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ) -> List[str]:
        """Retrieve a list of agent addresses using a specific protocol digest.

        This method queries the Almanac API to retrieve a list of agent addresses
        that are associated with a given protocol digest. The list can be optionally
        limited to a specified number of addresses.

        Args:
            protocol_digest (str): The protocol digest to search for, starting with "proto:".
            limit (int, optional): The maximum number of agent addresses to return.

        Returns:
            List[str]: A list of agent addresses using the specified protocol digest.
        """
        if not isinstance(protocol_digest, str) or not protocol_digest.startswith(
            "proto:"
        ):
            log(logger, logging.ERROR, f"Invalid protocol digest: {protocol_digest}")
            return []
        response = requests.post(
            url=ALMANAC_API_URL + "search",
            json={"text": protocol_digest[6:]},
            timeout=DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            data = response.json()
            agents = [agent["address"] for agent in data if agent["status"] == "local"]
            return agents[:limit]
        return []

    async def broadcast(
        self,
        destination_protocol: str,
        message: Model,
        limit: Optional[int] = DEFAULT_SEARCH_LIMIT,
        timeout: Optional[int] = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> List[MsgStatus]:
        """Broadcast a message to agents with a specific protocol.

        This asynchronous method broadcasts a given message to agents associated
        with a specific protocol. The message is sent to multiple agents concurrently.
        The schema digest of the message is used for verification.

        Args:
            destination_protocol (str): The protocol to filter agents by.
            message (Model): The message to broadcast.
            limit (int, optional): The maximum number of agents to send the message to.
            timeout (int, optional): The timeout for sending each message.

        Returns:
            List[MsgStatus]: A list of message delivery statuses.
        """
        agents = self.get_agents_by_protocol(
            destination_protocol, limit=limit, logger=self.logger
        )
        if not agents:
            self.logger.error(f"No active agents found for: {destination_protocol}")
            return []

        schema_digest = Model.build_schema_digest(message)
        futures = await asyncio.gather(
            *[
                self.send_raw(
                    address,
                    message.json(),
                    schema_digest,
                    timeout=timeout,
                )
                for address in agents
            ]
        )
        self.logger.debug(f"Sent {len(futures)} messages")
        return futures

    def _is_valid_interval_message(self, schema_digest: str) -> bool:
        """
        Check if the message is a valid interval message.

        Args:
            schema_digest (str): The schema digest of the message to check.

        Returns:
            bool: Whether the message is a valid interval message.
        """
        if self._interval_messages and schema_digest in self._interval_messages:
            return True
        return False

    async def send(
        self,
        destination: str,
        message: Model,
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> MsgStatus:
        """
        Send a message to the specified destination.

        Args:
            destination (str): The destination address to send the message to.
            message (Model): The message to be sent.
            sync (bool): Whether to send the message synchronously or asynchronously.
            timeout (Optional[int]): The optional timeout for sending the message, in seconds.

        Returns:
            MsgStatus: The delivery status of the message.
        """
        schema_digest = Model.build_schema_digest(message)
        message_type = type(message)

        # this is the internal send method
        # interval messages are set but we don't have access to replies,
        # message_received, or protocol

        if not self._is_valid_interval_message(schema_digest):
            self._logger.exception(
                f"Outgoing message {message_type} is not a valid interval message"
            )
            return MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Invalid interval message",
                destination=destination,
                endpoint="",
            )

        return await self.send_raw(
            destination,
            message.json(),
            schema_digest,
            sync=sync,
            timeout=timeout,
        )

    async def send_raw(
        self,
        destination: str,
        json_message: JsonStr,
        schema_digest: str,
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> MsgStatus:
        """
        Send a raw message to the specified destination.

        Args:
            destination (str): The destination name or address to send the message to.
            json_message (JsonStr): The JSON-encoded message to be sent.
            schema_digest (str): The schema digest of the message.
            message_type (Optional[Type[Model]]): The optional type of the message being sent.
            sync (bool): Whether to send the message synchronously or asynchronously.
            timeout (Optional[int]): The optional timeout for sending the message, in seconds.

        Returns:
            MsgStatus: The delivery status of the message.
        """
        self._session = self._session or uuid.uuid4()

        # Extract address from destination agent identifier if present
        _, _, destination_address = parse_identifier(destination)

        if destination_address:
            # Handle local dispatch of messages
            if dispatcher.contains(destination_address):
                await dispatcher.dispatch(
                    self.agent.address,
                    destination_address,
                    schema_digest,
                    json_message,
                    self._session,
                )
                return MsgStatus(
                    status=DeliveryStatus.DELIVERED,
                    detail="Message dispatched locally",
                    destination=destination_address,
                    endpoint="",
                )

            # Handle queries waiting for a response
            if destination_address in self._queries:
                self._queries[destination_address].set_result(
                    (json_message, schema_digest)
                )
                del self._queries[destination_address]
                return MsgStatus(
                    status=DeliveryStatus.DELIVERED,
                    detail="Sync message resolved",
                    destination=destination_address,
                    endpoint="",
                )

            self._outbound_messages[destination_address] = (json_message, schema_digest)

        result = await send_raw_exchange_envelope(
            self.agent,
            destination,
            self._resolver,
            schema_digest,
            self.protocol[0],
            json_message,
            logger=self._logger,
            timeout=timeout,
            session_id=self._session,
            sync=sync,
        )

        if isinstance(result, Envelope):
            return await dispatch_sync_response_envelope(result)

        return result


class Context(InternalContext):
    """
    Represents the reactive context in which messages are handled and processed.

    Attributes:
        storage (KeyValueStore): The key-value store for storage operations.
        ledger (LedgerClient): The client for interacting with the blockchain ledger.
        _resolver (Resolver): The resolver for address-to-endpoint resolution.
        _queries (Dict[str, asyncio.Future]): Dictionary mapping query senders to their
            response Futures.
        _session (Optional[uuid.UUID]): The session UUID.
        _replies (Optional[Dict[str, Dict[str, Type[Model]]]]): Dictionary of allowed reply digests
            for each type of incoming message.
        _interval_messages (Optional[Set[str]]): Set of message digests that may be sent by
            interval tasks.
        _message_received (Optional[MsgDigest]): The message digest received.
        _protocols (Optional[Dict[str, Protocol]]): Dictionary mapping all supported protocol
            digests to their corresponding protocols.
        _logger (Optional[logging.Logger]): The optional logger instance.

    Properties:
        logger (logging.Logger): The logger instance.
        protocols (Optional[Dict[str, Protocol]]): Dictionary mapping all supported protocol
            digests to their corresponding protocols.
        session (uuid.UUID): The session UUID.

    Methods:
        send(destination, message, timeout): Send a message to a destination.
        send_raw(destination, json_message, schema_digest, message_type, timeout):
            Send a message with the provided schema digest to a destination.
        broadcast(destination_protocol, message, limit, timeout): Broadcast a message
            to agents with a specific protocol.
    """

    def __init__(
        self,
        session: Optional[uuid.UUID] = None,
        queries: Dict[str, asyncio.Future] = None,
        replies: Optional[Dict[str, Dict[str, Type[Model]]]] = None,
        message_received: Optional[MsgDigest] = None,
        protocol: Optional[Tuple[str, Protocol]] = None,
        **kwargs,
    ):
        """
        Initialize the Context instance.

        Args:
            storage (KeyValueStore): The key-value store for storage operations.
            resolve (Resolver): The resolver for name-to-address resolution.
            ledger (LedgerClient): The ledger client for interacting with distributed ledgers.
            queries (Dict[str, asyncio.Future]): Dictionary mapping query senders to their
                response Futures.
            session (Optional[uuid.UUID]): The optional session UUID.
            replies (Optional[Dict[str, Dict[str, Type[Model]]]]): Dictionary of allowed replies
                for each type of incoming message.
            interval_messages (Optional[Set[str]]): The optional set of interval messages.
            message_received (Optional[MsgDigest]): The optional message digest received.
            wallet_messaging_client (Optional[Any]): The optional wallet messaging client.
            protocols (Optional[Dict[str, Protocol]]): The optional dictionary of protocols.
            logger (Optional[logging.Logger]): The optional logger instance.
        """
        super().__init__(**kwargs)
        self._session = session or None
        if queries is None:
            self._queries = {}
        self._replies = replies
        self._message_received = message_received
        self._protocol = protocol or ("", None)

    @property
    def protocol(self) -> Tuple[str, Protocol]:
        """
        Get the protocol associated with the context.

        Returns:
            Tuple[str, Protocol]: The protocol associated with the context.
        """
        return self._protocol

    def _is_valid_reply(self, message_type: Type[Model]) -> bool:
        """
        Check if the message type is a valid reply to the message received.

        Args:
            message_type (Type[Model]): The type of the message to check.

        Returns:
            bool: Whether the message type is a valid reply.
        """
        if not self._message_received:
            raise ValueError("No message received")

        if not self._replies:
            raise ValueError("No replies configured")

        received = self._message_received
        if received.schema_digest in self._replies:
            return message_type in self._replies[received.schema_digest]
        return False

    async def send(
        self,
        destination: str,
        message: Model,
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> MsgStatus:
        """
        Send a message to the specified destination.

        Args:
            destination (str): The destination address to send the message to.
            message (Model): The message to be sent.
            sync (bool): Whether to send the message synchronously or asynchronously.
            timeout (Optional[int]): The optional timeout for sending the message, in seconds.

        Returns:
            MsgStatus: The delivery status of the message.
        """
        schema_digest = Model.build_schema_digest(message)
        message_type = type(message)

        # at this point we have received a message and have built a context
        # replies, message_received, and protocol are set

        if schema_digest != ERROR_MESSAGE_DIGEST and not self._is_valid_reply(
            message_type
        ):
            self._logger.exception(
                f"Outgoing message {message_type} is not a valid reply"
                f"to {self._message_received.message}"
            )
            return MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Invalid reply",
                destination=destination,
                endpoint="",
            )

        return await self.send_raw(
            destination,
            message.json(),
            schema_digest,
            sync=sync,
            timeout=timeout,
        )

    async def send_wallet_message(
        self,
        destination: str,
        text: str,
        msg_type: int = 1,
    ):
        if self._wallet_messaging_client is not None:
            await self._wallet_messaging_client.send(destination, text, msg_type)
        else:
            self.logger.warning("Cannot send wallet message: no client available")


async def send_raw_exchange_envelope(
    sender: AgentRepresentation,
    destination: str,
    resolver: Resolver,
    schema_digest: str,
    protocol_digest: Optional[str],
    json_message: JsonStr,
    logger: Optional[logging.Logger] = None,
    timeout: int = 5,
    session_id: Optional[uuid.UUID] = None,
    sync: bool = False,
) -> Union[MsgStatus, Envelope]:
    """
    Standalone function to send a raw exchange envelope to an agent.

    Args:
        sender (AgentRepresentation): The representation of an agent.
        destination (str): The destination address to send the message to.
        resolver (Resolver): The resolver for address-to-endpoint resolution.
        schema_digest (str): The schema digest of the message.
        protocol_digest (Optional[str]): The protocol digest of the message.
        json_message (JsonStr): The JSON-encoded message to be sent.
        logger (Optional[logging.Logger]): The optional logger instance.
        timeout (int): The timeout for sending the message, in seconds.
        session_id (Optional[uuid.UUID]): The optional session ID.
        sync (bool): Whether to send the message synchronously or asynchronously.

    Returns:
        Union[MsgStatus, Envelope]: The delivery status of the message, or in the case of a
        successful synchronous message, the response envelope.
    """
    # Resolve the destination address and endpoint ('destination' can be a name or address)
    destination_address, endpoints = await resolver.resolve(destination)
    if len(endpoints) == 0:
        log(
            logger,
            logging.ERROR,
            f"Unable to resolve destination endpoint for address {destination}",
        )

        return MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Unable to resolve destination endpoint",
            destination=destination,
            endpoint="",
        )

    # Calculate when the envelope expires
    expires = int(time()) + timeout

    # Handle external dispatch of messages
    env = Envelope(
        version=1,
        sender=sender.address,
        target=destination_address,
        session=session_id or uuid.uuid4(),
        schema_digest=schema_digest,
        protocol_digest=protocol_digest,
        expires=expires,
    )
    env.encode_payload(json_message)
    env.sign(sender.sign_digest)

    headers = {"content-type": "application/json"}
    if sync:
        headers["x-uagents-connection"] = "sync"

    for endpoint in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers=headers,
                    data=env.json(),
                ) as resp:
                    success = resp.status == 200
                    if success:
                        if sync:
                            return Envelope.parse_obj(await resp.json())

                        return MsgStatus(
                            status=DeliveryStatus.DELIVERED,
                            detail="Message successfully delivered via HTTP",
                            destination=destination_address,
                            endpoint=endpoint,
                        )
                log(
                    logger,
                    logging.WARNING,
                    f"Failed to send message to {destination_address} @ {endpoint}: "
                    + (await resp.text()),
                )
        except aiohttp.ClientConnectorError as ex:
            log(logger, logging.WARNING, f"Failed to connect to {endpoint}: {ex}")

        except ValidationError as ex:
            log(
                logger,
                logging.WARNING,
                f"Sync message to {destination} @ {endpoint} got invalid response: {ex}",
            )

        except Exception as ex:
            log(
                logger,
                logging.WARNING,
                f"Failed to send message to {destination} @ {endpoint}: {ex}",
            )

    log(logger, logging.ERROR, f"Failed to deliver message to {destination}")

    return MsgStatus(
        status=DeliveryStatus.FAILED,
        detail="Message delivery failed",
        destination=destination,
        endpoint="",
    )


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
