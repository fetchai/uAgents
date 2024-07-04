"""Agent Context and Message Handling"""

from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
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

import requests
from cosmpy.aerial.client import LedgerClient
from typing_extensions import deprecated
from uagents.communication import (
    DeliveryStatus,
    Dispenser,
    MsgDigest,
    MsgStatus,
    dispatch_local_message,
    dispatch_sync_response_envelope,
)
from uagents.config import (
    ALMANAC_API_URL,
    DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    DEFAULT_SEARCH_LIMIT,
)
from uagents.dispatch import JsonStr, dispatcher
from uagents.envelope import Envelope
from uagents.models import ErrorMessage, Model
from uagents.resolver import Resolver, parse_identifier
from uagents.storage import KeyValueStore
from uagents.utils import log

if TYPE_CHECKING:
    from uagents.agent import AgentRepresentation
    from uagents.protocol import Protocol

IntervalCallback = Callable[["Context"], Awaitable[None]]
MessageCallback = Callable[["Context", str, Any], Awaitable[None]]
EventCallback = Callable[["Context"], Awaitable[None]]
WalletMessageCallback = Callable[["Context", Any], Awaitable[None]]


ERROR_MESSAGE_DIGEST = Model.build_schema_digest(ErrorMessage)


class Context(ABC):
    # pylint: disable=unnecessary-pass
    """
    Represents the context in which messages are handled and processed.

    Properties:
        agent (AgentRepresentation): The agent representation associated with the context.
        storage (KeyValueStore): The key-value store for storage operations.
        ledger (LedgerClient): The client for interacting with the blockchain ledger.
        logger (logging.Logger): The logger instance.

    Methods:
        get_agents_by_protocol(protocol_digest, limit, logger): Retrieve a list of agent addresses
            using a specific protocol digest.
        broadcast(destination_protocol, message, limit, timeout): Broadcast a message
            to agents with a specific protocol.
        send(destination, message, timeout): Send a message to a destination.
        send_raw(destination, json_message, schema_digest, message_type, timeout):
            Send a message with the provided schema digest to a destination.
    """

    @property
    @abstractmethod
    def agent(self) -> AgentRepresentation:
        """
        Get the agent representation associated with the context.

        Returns:
            AgentRepresentation: The agent representation.
        """
        pass

    @property
    @abstractmethod
    def storage(self) -> KeyValueStore:
        """
        Get the key-value store associated with the context.

        Returns:
            KeyValueStore: The key-value store.
        """
        pass

    @property
    @abstractmethod
    def ledger(self) -> LedgerClient:
        """
        Get the ledger client associated with the context.

        Returns:
            LedgerClient: The ledger client.
        """
        pass

    @property
    @abstractmethod
    def logger(self) -> logging.Logger:
        """
        Get the logger instance associated with the context.

        Returns:
            logging.Logger: The logger instance.
        """
        pass

    @property
    @abstractmethod
    def session(self) -> Union[uuid.UUID, None]:
        """
        Get the session UUID associated with the context.

        Returns:
            uuid.UUID: The session UUID.
        """
        pass

    @abstractmethod
    def get_agents_by_protocol(
        self,
        protocol_digest: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
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
        pass

    @abstractmethod
    async def broadcast(
        self,
        destination_protocol: str,
        message: Model,
        limit: int = DEFAULT_SEARCH_LIMIT,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def send_raw(
        self,
        destination: str,
        message_schema_digest: str,
        message_body: JsonStr,
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        protocol_digest: Optional[str] = None,
        queries: Optional[Dict[str, asyncio.Future]] = None,
    ) -> MsgStatus:
        """
        Send a message to the specified destination where the message body and
        message schema digest are sent separately.

        Args:
            destination (str): The destination address to send the message to.
            message_schema_digest (str): The schema digest of the message to be sent.
            message_body (JsonStr): The JSON-encoded message body to be sent.
            sync (bool): Whether to send the message synchronously or asynchronously.
            timeout (Optional[int]): The optional timeout for sending the message, in seconds.
            protocol_digest (Optional[str]): The protocol digest of the message to be sent.
            queries (Optional[Dict[str, asyncio.Future]]): The dictionary of queries to resolve.

        Returns:
            MsgStatus: The delivery status of the message.
        """
        pass

    @abstractmethod
    async def send_wallet_message(
        self,
        destination: str,
        text: str,
        msg_type: int = 1,
    ):
        """
        Send a message to the wallet of the specified destination.

        Args:
            destination (str): The destination address to send the message to.
            text (str): The text of the message to be sent.
            msg_type (int): The type of the message to be sent.

        Returns:
            None
        """
        pass


class InternalContext(Context):
    """
    Represents the agent internal context for proactive behaviour.
    """

    def __init__(
        self,
        agent: AgentRepresentation,
        storage: KeyValueStore,
        ledger: LedgerClient,
        resolver: Resolver,
        dispenser: Dispenser,
        interval_messages: Optional[Set[str]] = None,
        wallet_messaging_client: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._agent = agent
        self._storage = storage
        self._ledger = ledger
        self._resolver = resolver
        self._dispenser = dispenser
        self._logger = logger
        self._session: Optional[uuid.UUID] = None
        self._interval_messages = interval_messages
        self._wallet_messaging_client = wallet_messaging_client
        self._outbound_messages: Dict[str, Tuple[JsonStr, str]] = {}

    @property
    def agent(self) -> AgentRepresentation:
        return self._agent

    @property
    def storage(self) -> KeyValueStore:
        return self._storage

    @property
    def ledger(self) -> LedgerClient:
        return self._ledger

    @property
    def logger(self) -> Union[logging.Logger, None]:
        return self._logger

    @property
    def session(self) -> Union[uuid.UUID, None]:
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

    @property
    @deprecated("Please use `ctx.agent.address` instead.")
    def address(self) -> str:
        """
        Get the agent address associated with the context.
        This is a deprecated property and will be removed in a future release.
        Please use the `ctx.agent.address` property instead.

        Returns:
            str: The agent address.
        """
        return self.agent.address

    def get_agents_by_protocol(
        self,
        protocol_digest: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        logger: Optional[logging.Logger] = None,
    ) -> List[str]:
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
            agents = [agent["address"] for agent in data if agent["status"] == "active"]
            return agents[:limit]
        return []

    async def broadcast(
        self,
        destination_protocol: str,
        message: Model,
        limit: int = DEFAULT_SEARCH_LIMIT,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> List[MsgStatus]:
        agents = self.get_agents_by_protocol(
            destination_protocol, limit=limit, logger=self.logger
        )
        if not agents:
            log(
                self.logger,
                logging.ERROR,
                f"No active agents found for: {destination_protocol}",
            )
            return []

        if self.agent.address in agents:
            agents.remove(self.agent.address)
        futures = await asyncio.gather(
            *[
                self.send(
                    address,
                    message,
                    sync=False,
                    timeout=timeout,
                )
                for address in agents
            ]
        )
        log(self.logger, logging.DEBUG, f"Sent {len(futures)} messages")
        return futures

    def _is_valid_interval_message(self, schema_digest: str) -> bool:
        """
        Check if the message is a valid interval message.

        Args:
            schema_digest (str): The schema digest of the message to check.

        Returns:
            bool: Whether the message is a valid interval message.
        """
        if self._interval_messages:
            return schema_digest in self._interval_messages
        return True

    async def send(
        self,
        destination: str,
        message: Model,
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> MsgStatus:
        """
        This is the pro-active send method which is used in on_event and
        on_interval methods. In these methods, interval messages are set but
        we don't have access properties that are only necessary in re-active
        contexts, like 'replies', 'message_received', or 'protocol'.
        """
        self._session = None
        schema_digest = Model.build_schema_digest(message)
        message_body = message.model_dump_json()

        if not self._is_valid_interval_message(schema_digest):
            log(self.logger, logging.ERROR, f"Invalid interval message: {message}")
            return MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Invalid interval message",
                destination=destination,
                endpoint="",
                session=self._session,
            )

        return await self.send_raw(
            destination,
            schema_digest,
            message_body,
            sync=sync,
            timeout=timeout,
        )

    async def send_raw(
        self,
        destination: str,
        message_schema_digest: str,
        message_body: JsonStr,
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        protocol_digest: Optional[str] = None,
        queries: Optional[Dict[str, asyncio.Future]] = None,
    ) -> MsgStatus:
        self._session = self._session or uuid.uuid4()

        # Extract address from destination agent identifier if present
        _, parsed_name, parsed_address = parse_identifier(destination)

        if parsed_address:
            # Handle local dispatch of messages
            if dispatcher.contains(parsed_address):
                return await dispatch_local_message(
                    self.agent.address,
                    parsed_address,
                    message_schema_digest,
                    message_body,
                    self._session,
                )

            # Handle sync dispatch of messages
            if queries and parsed_address in queries:
                queries[parsed_address].set_result(
                    (message_body, message_schema_digest)
                )
                del queries[parsed_address]
                return MsgStatus(
                    status=DeliveryStatus.DELIVERED,
                    detail="Sync message resolved",
                    destination=parsed_address,
                    endpoint="",
                    session=self._session,
                )

            self._outbound_messages[parsed_address] = (
                message_body,
                message_schema_digest,
            )

        # Resolve destination address or name using the resolver
        destination_address, endpoints = await self._resolver.resolve(
            parsed_address or parsed_name
        )

        if not endpoints or not destination_address:
            log(self.logger, logging.ERROR, "Unable to resolve destination endpoint")
            return MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Unable to resolve destination endpoint",
                destination=destination,
                endpoint="",
                session=self._session,
            )

        # Calculate when the envelope expires
        expires = int(time()) + timeout

        # Handle external dispatch of messages
        env = Envelope(
            version=1,
            sender=self.agent.address,
            target=destination_address,
            session=self._session,
            schema_digest=message_schema_digest,
            protocol_digest=protocol_digest,
            expires=expires,
        )
        env.encode_payload(message_body)
        env.sign(self.agent.sign_digest)

        # Create awaitable future for MsgStatus and sync response
        fut = asyncio.Future()

        self._queue_envelope(env, endpoints, fut, sync)

        try:
            result = await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            log(self.logger, logging.ERROR, "Timeout waiting for dispense response")
            return MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Timeout waiting for response",
                destination=destination,
                endpoint="",
                session=self._session,
            )

        if isinstance(result, Envelope):
            return await dispatch_sync_response_envelope(result)

        return result

    def _queue_envelope(
        self,
        envelope: Envelope,
        endpoints: List[str],
        response_future: asyncio.Future,
        sync: bool = False,
    ):
        """
        Queue an envelope for processing.

        Args:
            envelope (Envelope): The envelope to queue.
        """
        self._dispenser.add_envelope(envelope, endpoints, response_future, sync)

    async def send_wallet_message(
        self,
        destination: str,
        text: str,
        msg_type: int = 1,
    ):  # TODO: restructure wallet messaging
        if self._wallet_messaging_client is not None:
            await self._wallet_messaging_client.send(destination, text, msg_type)
        else:
            log(
                self.logger,
                logging.WARNING,
                "Cannot send wallet message: no client available",
            )


class ExternalContext(InternalContext):
    """
    Represents the reactive context in which messages are handled and processed.

    Attributes:
        _queries (Dict[str, asyncio.Future]): Dictionary mapping query senders to their
            response Futures.
        _session (Optional[uuid.UUID]): The session UUID.
        _replies (Optional[Dict[str, Dict[str, Type[Model]]]]): Dictionary of allowed reply digests
            for each type of incoming message.
        _message_received (Optional[MsgDigest]): The message digest received.
        _protocol (Optional[Tuple[str, Protocol]]): The supported protocol digest
            and the corresponding protocol.
    """

    def __init__(
        self,
        message_received: MsgDigest,
        session: Optional[uuid.UUID] = None,
        queries: Optional[Dict[str, asyncio.Future]] = None,
        replies: Optional[Dict[str, Dict[str, Type[Model]]]] = None,
        protocol: Optional[Tuple[str, Protocol]] = None,
        **kwargs,
    ):
        """
        Initialize the ExternalContext instance and attributes needed from the InternalContext.

        Args:
            message_received (MsgDigest): The optional message digest received.
            queries (Dict[str, asyncio.Future]): Dictionary mapping query senders to their
                response Futures.
            session (Optional[uuid.UUID]): The optional session UUID.
            replies (Optional[Dict[str, Dict[str, Type[Model]]]]): Dictionary of allowed replies
                for each type of incoming message.
            protocol (Optional[Tuple[str, Protocol]]): The optional Tuple of protocols.
        """
        super().__init__(**kwargs)
        self._session = session or None
        self._queries = queries or {}
        self._replies = replies
        self._message_received = message_received
        self._protocol = protocol or ("", None)

    def _is_valid_reply(self, message_schema_digest: str) -> bool:
        """
        Check if the message type is a valid reply to the message received.

        Args:
            message_type (Type[Model]): The type of the message to check.

        Returns:
            bool: Whether the message type is a valid reply.
        """
        if message_schema_digest == ERROR_MESSAGE_DIGEST:
            return True

        if not self._message_received:
            raise ValueError("No message received")

        if not self._replies:
            return True

        received = self._message_received
        if received.schema_digest in self._replies:
            return message_schema_digest in self._replies[received.schema_digest]
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

        # This is the re-active send method
        # at this point we have received a message and have built a context
        # replies, message_received, and protocol are set

        if not self._is_valid_reply(schema_digest):
            log(
                self.logger,
                logging.ERROR,
                f"Outgoing message '{message_type}' is not a valid reply"
                f"to received message: {self._message_received.schema_digest}",
            )
            return MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Invalid reply",
                destination=destination,
                endpoint="",
                session=self._session,
            )

        return await self.send_raw(
            destination,
            schema_digest,
            message.model_dump_json(),
            sync=sync,
            timeout=timeout,
            protocol_digest=self._protocol[0],
            queries=self._queries,
        )
