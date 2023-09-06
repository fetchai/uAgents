"""Agent Context and Message Handling"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from time import time
from typing import (
    Dict,
    List,
    Set,
    Optional,
    Callable,
    Any,
    Awaitable,
    Type,
    TYPE_CHECKING,
)

import aiohttp
import requests
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet

from uagents.config import (
    ALMANAC_API_URL,
    DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    DEFAULT_SEARCH_LIMIT,
)
from uagents.crypto import Identity
from uagents.dispatch import JsonStr, dispatcher
from uagents.envelope import Envelope
from uagents.models import ErrorMessage, Model
from uagents.resolver import Resolver
from uagents.storage import KeyValueStore

if TYPE_CHECKING:
    from uagents.protocol import Protocol

IntervalCallback = Callable[["Context"], Awaitable[None]]
MessageCallback = Callable[["Context", str, Any], Awaitable[None]]
EventCallback = Callable[["Context"], Awaitable[None]]


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


ERROR_MESSAGE_DIGEST = Model.build_schema_digest(ErrorMessage)


class Context:
    """
    Represents the context in which messages are handled and processed.

    Attributes:
        storage (KeyValueStore): The key-value store for storage operations.
        wallet (LocalWallet): The agent's wallet for transacting on the ledger.
        ledger (LedgerClient): The client for interacting with the blockchain ledger.
        _name (Optional[str]): The name of the agent.
        _address (str): The address of the agent.
        _resolver (Resolver): The resolver for address-to-endpoint resolution.
        _identity (Identity): The agent's identity.
        _queries (Dict[str, asyncio.Future]): Dictionary mapping query senders to their
        response Futures.
        _session (Optional[uuid.UUID]): The session UUID.
        _replies (Optional[Dict[str, Set[Type[Model]]]]): Dictionary of allowed reply digests
        for each type of incoming message.
        _interval_messages (Optional[Set[str]]): Set of message digests that may be sent by
        interval tasks.
        _message_received (Optional[MsgDigest]): The message digest received.
        _protocols (Optional[Dict[str, Protocol]]): Dictionary mapping all supported protocol
        digests to their corresponding protocols.
        _logger (Optional[logging.Logger]): The optional logger instance.

    Properties:
        name (str): The name of the agent.
        address (str): The address of the agent.
        logger (logging.Logger): The logger instance.
        protocols (Optional[Dict[str, Protocol]]): Dictionary mapping all supported protocol
        digests to their corresponding protocols.
        session (uuid.UUID): The session UUID.

    Methods:
        get_message_protocol(message_schema_digest): Get the protocol associated
        with a message schema digest.
        send(destination, message, timeout): Send a message to a destination.
        send_raw(destination, json_message, schema_digest, message_type, timeout): Send a message
        with the provided schema digest to a destination.
        experimental_broadcast(destination_protocol, message, limit, timeout): Broadcast a message
        to agents with a specific protocol.

    """

    def __init__(
        self,
        address: str,
        name: Optional[str],
        storage: KeyValueStore,
        resolve: Resolver,
        identity: Identity,
        wallet: LocalWallet,
        ledger: LedgerClient,
        queries: Dict[str, asyncio.Future],
        session: Optional[uuid.UUID] = None,
        replies: Optional[Dict[str, Set[Type[Model]]]] = None,
        interval_messages: Optional[Set[str]] = None,
        message_received: Optional[MsgDigest] = None,
        protocols: Optional[Dict[str, Protocol]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the Context instance.

        Args:
            address (str): The address of the context.
            name (Optional[str]): The optional name associated with the context.
            storage (KeyValueStore): The key-value store for storage operations.
            resolve (Resolver): The resolver for name-to-address resolution.
            identity (Identity): The identity associated with the context.
            wallet (LocalWallet): The local wallet instance for managing identities.
            ledger (LedgerClient): The ledger client for interacting with distributed ledgers.
            queries (Dict[str, asyncio.Future]): Dictionary mapping query senders to their response
            Futures.
            session (Optional[uuid.UUID]): The optional session UUID.
            replies (Optional[Dict[str, Set[Type[Model]]]]): Optional dictionary of reply models.
            interval_messages (Optional[Set[str]]): The optional set of interval messages.
            message_received (Optional[MsgDigest]): The optional message digest received.
            protocols (Optional[Dict[str, Protocol]]): The optional dictionary of protocols.
            logger (Optional[logging.Logger]): The optional logger instance.
        """
        self.storage = storage
        self.wallet = wallet
        self.ledger = ledger
        self._name = name
        self._address = str(address)
        self._resolver = resolve
        self._identity = identity
        self._queries = queries
        self._session = session or None
        self._replies = replies
        self._interval_messages = interval_messages
        self._message_received = message_received
        self._protocols = protocols or {}
        self._logger = logger

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
    def logger(self) -> logging.Logger:
        """
        Get the logger instance associated with the context.

        Returns:
            logging.Logger: The logger instance.
        """
        return self._logger

    @property
    def protocols(self) -> Optional[Dict[str, Protocol]]:
        """
        Get the dictionary of protocols associated with the context.

        Returns:
            Optional[Dict[str, Protocol]]: The dictionary of protocols.
        """
        return self._protocols

    @property
    def session(self) -> uuid.UUID:
        """
        Get the session UUID associated with the context.

        Returns:
            uuid.UUID: The session UUID.
        """
        return self._session

    def get_message_protocol(self, message_schema_digest) -> Optional[str]:
        """
        Get the protocol associated with a given message schema digest.

        Args:
            message_schema_digest (str): The schema digest of the message.

        Returns:
            Optional[str]: The protocol digest associated with the message schema digest,
            or None if not found.
        """
        for protocol_digest, protocol in self._protocols.items():
            for reply_models in protocol.replies.values():
                if message_schema_digest in reply_models:
                    return protocol_digest
        return None

    def get_agents_by_protocol(
        self, protocol_digest: str, limit: Optional[int] = None
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
            self.logger.error(f"Invalid protocol digest: {protocol_digest}")
            raise ValueError("Invalid protocol digest")
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

    async def send(
        self,
        destination: str,
        message: Model,
        timeout: Optional[int] = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ):
        """
        Send a message to the specified destination.

        Args:
            destination (str): The destination address to send the message to.
            message (Model): The message to be sent.
            timeout (Optional[int]): The optional timeout for sending the message, in seconds.
        """
        schema_digest = Model.build_schema_digest(message)
        await self.send_raw(
            destination,
            message.json(),
            schema_digest,
            message_type=type(message),
            timeout=timeout,
        )

    async def experimental_broadcast(
        self,
        destination_protocol: str,
        message: Model,
        limit: Optional[int] = DEFAULT_SEARCH_LIMIT,
        timeout: Optional[int] = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ):
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
            None
        """
        agents = self.get_agents_by_protocol(destination_protocol, limit=limit)
        if not agents:
            self.logger.error(f"No active agents found for: {destination_protocol}")
            return
        schema_digest = Model.build_schema_digest(message)
        futures = await asyncio.gather(
            *[
                self.send_raw(
                    address,
                    message.json(),
                    schema_digest,
                    message_type=type(message),
                    timeout=timeout,
                )
                for address in agents
            ]
        )
        self.logger.debug(f"Sent {len(futures)} messages")

    async def send_raw(
        self,
        destination: str,
        json_message: JsonStr,
        schema_digest: str,
        message_type: Optional[Type[Model]] = None,
        timeout: Optional[int] = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ):
        """
        Send a raw message to the specified destination.

        Args:
            destination (str): The destination address to send the message to.
            json_message (JsonStr): The JSON-encoded message to be sent.
            schema_digest (str): The schema digest of the message.
            message_type (Optional[Type[Model]]): The optional type of the message being sent.
            timeout (Optional[int]): The optional timeout for sending the message, in seconds.
        """
        # Check if this message is a reply
        if (
            self._message_received is not None
            and self._replies
            and schema_digest != ERROR_MESSAGE_DIGEST
        ):
            received = self._message_received
            if received.schema_digest in self._replies:
                # Ensure the reply is valid
                if schema_digest not in self._replies[received.schema_digest]:
                    self._logger.exception(
                        f"Outgoing message {message_type or ''} "
                        f"is not a valid reply to {received.message}"
                    )
                    return

        # Check if this message is a valid interval message
        if self._message_received is None and self._interval_messages:
            if schema_digest not in self._interval_messages:
                self._logger.exception(
                    f"Outgoing message {message_type} is not a valid interval message"
                )
                return

        # Handle local dispatch of messages
        if dispatcher.contains(destination):
            await dispatcher.dispatch(
                self.address, destination, schema_digest, json_message, self._session
            )
            return

        # Handle queries waiting for a response
        if destination in self._queries:
            self._queries[destination].set_result((json_message, schema_digest))
            del self._queries[destination]
            return

        # Resolve the endpoint
        destination_address, endpoint = await self._resolver.resolve(destination)
        if endpoint is None:
            self._logger.exception(
                f"Unable to resolve destination endpoint for address {destination}"
            )
            return

        # Calculate when the envelope expires
        expires = int(time()) + timeout

        # Handle external dispatch of messages
        env = Envelope(
            version=1,
            sender=self.address,
            target=destination_address,
            session=self._session or uuid.uuid4(),
            schema_digest=schema_digest,
            protocol_digest=self.get_message_protocol(schema_digest),
            expires=expires,
        )
        env.encode_payload(json_message)
        env.sign(self._identity)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers={"content-type": "application/json"},
                    data=env.json(),
                ) as resp:
                    success = resp.status == 200
                if not success:
                    self._logger.exception(
                        f"Unable to send envelope to {destination_address} @ {endpoint}"
                    )
        except aiohttp.ClientConnectorError as ex:
            self._logger.exception(f"Failed to connect to {endpoint}: {ex}")
        except Exception as ex:
            self._logger.exception(f"Failed to send message to {destination}: {ex}")
