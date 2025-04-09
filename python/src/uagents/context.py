"""Agent Context and Message Handling"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from time import time
from typing import TYPE_CHECKING, Any

import requests
from cosmpy.aerial.client import LedgerClient
from pydantic.v1 import ValidationError
from uagents_core.envelope import Envelope
from uagents_core.identity import parse_identifier
from uagents_core.models import ERROR_MESSAGE_DIGEST, ErrorMessage, Model
from uagents_core.types import DeliveryStatus, MsgStatus

from uagents.communication import dispatch_local_message
from uagents.config import (
    ALMANAC_API_URL,
    DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    DEFAULT_SEARCH_LIMIT,
)
from uagents.dispatch import dispatcher
from uagents.resolver import Resolver
from uagents.storage import KeyValueStore
from uagents.types import EnvelopeHistory, EnvelopeHistoryEntry, JsonStr, MsgInfo
from uagents.utils import log

if TYPE_CHECKING:
    from uagents.agent import AgentRepresentation
    from uagents.communication import Dispenser
    from uagents.protocol import Protocol


class Context(ABC):
    """
    Represents the context in which messages are handled and processed.

    Properties:
        agent (AgentRepresentation): The agent representation associated with the context.
        storage (KeyValueStore): The key-value store for storage operations.
        ledger (LedgerClient): The client for interacting with the blockchain ledger.
        logger (logging.Logger): The logger instance.
        session (uuid.UUID): The session UUID associated with the context.

    Methods:
        get_agents_by_protocol(protocol_digest, limit, logger): Retrieve a list of agent addresses
            using a specific protocol digest.
        broadcast(destination_protocol, message, limit, timeout): Broadcast a message
            to agents with a specific protocol.
        session_history: Get the message history associated with the context session.
        send(destination, message, timeout): Send a message to a destination.
        send_raw(destination, json_message, schema_digest, message_type, timeout):
            Send a message with the provided schema digest to a destination.
    """

    @property
    @abstractmethod
    def agent(self) -> "AgentRepresentation":
        """
        Get the agent representation associated with the context.

        Returns:
            AgentRepresentation: The agent representation.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def storage(self) -> KeyValueStore:
        """
        Get the key-value store associated with the context.

        Returns:
            KeyValueStore: The key-value store.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def ledger(self) -> LedgerClient:
        """
        Get the ledger client associated with the context.

        Returns:
            LedgerClient: The ledger client.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def logger(self) -> logging.Logger:
        """
        Get the logger instance associated with the context.

        Returns:
            logging.Logger: The logger instance.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def session(self) -> uuid.UUID:
        """
        Get the session UUID associated with the context.

        Returns:
            uuid.UUID: The session UUID.
        """
        raise NotImplementedError

    @abstractmethod
    def get_agents_by_protocol(
        self,
        protocol_digest: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        logger: logging.Logger | None = None,
    ) -> list[str]:
        """Retrieve a list of agent addresses using a specific protocol digest.

        This method queries the Almanac API to retrieve a list of agent addresses
        that are associated with a given protocol digest. The list can be optionally
        limited to a specified number of addresses.

        Args:
            protocol_digest (str): The protocol digest to search for, starting with "proto:".
            limit (int, optional): The maximum number of agent addresses to return.

        Returns:
            list[str]: A list of agent addresses using the specified protocol digest.
        """
        raise NotImplementedError

    @abstractmethod
    async def broadcast(
        self,
        destination_protocol: str,
        message: Model,
        limit: int = DEFAULT_SEARCH_LIMIT,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> list[MsgStatus]:
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
            list[MsgStatus]: A list of message delivery statuses.
        """
        raise NotImplementedError

    @abstractmethod
    def session_history(self) -> list[EnvelopeHistoryEntry] | None:
        """
        Get the message history associated with the context session.

        Returns:
            list[EnvelopeHistoryEntry] | None: The message history.
        """
        pass

    @abstractmethod
    async def send(
        self,
        destination: str,
        message: Model,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> MsgStatus:
        """
        Send a message to the specified destination.

        Args:
            destination (str): The destination address to send the message to.
            message (Model): The message to be sent.
            timeout (int, optional): The timeout for sending the message, in seconds.

        Returns:
            MsgStatus: The delivery status of the message.
        """
        raise NotImplementedError

    @abstractmethod
    async def send_raw(
        self,
        destination: str,
        message_schema_digest: str,
        message_body: JsonStr,
        sync: bool = False,
        wait_for_response: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        protocol_digest: str | None = None,
        queries: dict[str, asyncio.Future] | None = None,
    ) -> MsgStatus:
        """
        Send a message to the specified destination where the message body and
        message schema digest are sent separately.

        Args:
            destination (str): The destination address to send the message to.
            message_schema_digest (str): The schema digest of the message to be sent.
            message_body (JsonStr): The JSON-encoded message body to be sent.
            sync (bool): Whether to send the message synchronously or asynchronously.
            wait_for_response (bool): Whether to wait for a response to the message.
            timeout (int, optional): The optional timeout for sending the message, in seconds.
            protocol_digest (str, optional): The protocol digest of the message to be sent.
            queries (dict[str, asyncio.Future] | None): The dictionary of queries to resolve.

        Returns:
            MsgStatus: The delivery status of the message.
        """
        raise NotImplementedError

    @abstractmethod
    async def send_and_receive(
        self,
        destination: str,
        message: Model,
        response_type: type[Model] | set[type[Model]],
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> tuple[Model | None, MsgStatus]:
        """
        Send a message to the specified destination and receive a response.

        Args:
            destination (str): The destination address to send the message to.
            message (Model): The message to be sent.
            response_type (type[Model] | set[type[Model]]): The type(s) of the response message.
            sync (bool): Whether to send the message synchronously or asynchronously.
            timeout (int): The timeout for sending the message, in seconds.

        Returns:
            tuple[Model | None, MsgStatus]: The response message if received and delivery status
        """
        raise NotImplementedError

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
        raise NotImplementedError


class InternalContext(Context):
    """Represents the agent internal context for proactive behaviour."""

    def __init__(
        self,
        agent: "AgentRepresentation",
        storage: KeyValueStore,
        ledger: LedgerClient,
        resolver: Resolver,
        dispenser: "Dispenser",
        session: uuid.UUID | None = None,
        interval_messages: set[str] | None = None,
        wallet_messaging_client: Any | None = None,
        message_history: EnvelopeHistory | None = None,
        logger: logging.Logger | None = None,
    ):
        self._agent = agent
        self._storage = storage
        self._ledger = ledger
        self._resolver = resolver
        self._dispenser = dispenser
        self._logger = logger
        self._session = session or uuid.uuid4()
        self._interval_messages = interval_messages
        self._wallet_messaging_client = wallet_messaging_client
        self._message_history = message_history
        self._outbound_messages: dict[str, list[tuple[JsonStr, str]]] = {}

    @property
    def agent(self) -> "AgentRepresentation":
        return self._agent

    @property
    def storage(self) -> KeyValueStore:
        return self._storage

    @property
    def ledger(self) -> LedgerClient:
        return self._ledger

    @property
    def logger(self) -> logging.Logger | None:
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
    def outbound_messages(self) -> dict[str, list[tuple[JsonStr, str]]]:
        """
        Get the dictionary of outbound messages associated with the context.

        Returns:
            dict[str, list[tuple[JsonStr, str]]]: The dictionary of outbound messages.
        """
        return self._outbound_messages

    def session_history(self) -> list[EnvelopeHistoryEntry] | None:
        """
        Get the message history associated with the context session.

        Returns:
            list[EnvelopeHistoryEntry] | None: The session history.
        """
        if self._message_history is None:
            log(self.logger, logging.ERROR, "No session history available")
            return None
        return self._message_history.get_session_messages(self._session)

    def get_agents_by_protocol(
        self,
        protocol_digest: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        logger: logging.Logger | None = None,
    ) -> list[str]:
        if not isinstance(protocol_digest, str) or not protocol_digest.startswith(
            "proto:"
        ):
            log(logger, logging.ERROR, f"Invalid protocol digest: {protocol_digest}")
            return []
        almanac_api_url = getattr(
            getattr(self._resolver, "_almanac_api_resolver", None),
            "_almanac_api_url",
            ALMANAC_API_URL,
        )
        response = requests.post(
            url=almanac_api_url + "/search",
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
    ) -> list[MsgStatus]:
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
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> MsgStatus:
        """
        This is the pro-active send method which is used in on_event and
        on_interval methods. In these methods, interval messages are set but
        we don't have access properties that are only necessary in re-active
        contexts, like 'replies', 'message_received', or 'protocol'.
        """
        schema_digest: str = Model.build_schema_digest(message)
        message_body: JsonStr = message.model_dump_json()

        if not self._is_valid_interval_message(schema_digest):
            log(
                logger=self.logger,
                level=logging.ERROR,
                message=f"Invalid interval message: {message}",
            )
            return MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Invalid interval message",
                destination=destination,
                endpoint="",
                session=self._session,
            )

        return await self.send_raw(
            destination=destination,
            message_schema_digest=schema_digest,
            message_body=message_body,
            timeout=timeout,
        )

    async def send_raw(
        self,
        destination: str,
        message_schema_digest: str,
        message_body: JsonStr,
        sync: bool = False,
        wait_for_response: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        protocol_digest: str | None = None,
        queries: dict[str, asyncio.Future] | None = None,
    ) -> MsgStatus:
        # Extract address from destination agent identifier if present
        _, _, parsed_address = parse_identifier(destination)

        result = None
        if parsed_address:
            if sync or wait_for_response:
                dispatcher.register_pending_response(
                    sender=self.agent.address,
                    destination=parsed_address,
                    session=self._session,
                )
            # Handle local dispatch of messages
            if dispatcher.contains(parsed_address):
                result = await dispatch_local_message(
                    sender=self.agent.address,
                    destination=parsed_address,
                    schema_digest=message_schema_digest,
                    message=message_body,
                    session_id=self._session,
                )

            # Handle sync dispatch of messages
            elif queries and parsed_address in queries:
                queries[parsed_address].set_result(
                    (message_body, message_schema_digest)
                )
                del queries[parsed_address]
                result = MsgStatus(
                    status=DeliveryStatus.DELIVERED,
                    detail="Sync message resolved",
                    destination=parsed_address,
                    endpoint="",
                    session=self._session,
                )

            if parsed_address in self._outbound_messages:
                self._outbound_messages[parsed_address].append(
                    (message_body, message_schema_digest)
                )
            else:
                self._outbound_messages[parsed_address] = [
                    (message_body, message_schema_digest)
                ]

        if result is None:
            # Resolve destination using the resolver
            destination_address, endpoints = await self._resolver.resolve(destination)

            if not endpoints or not destination_address:
                log(
                    logger=self.logger,
                    level=logging.ERROR,
                    message=f"Unable to resolve destination endpoint for agent: {destination}",
                )
                result = MsgStatus(
                    status=DeliveryStatus.FAILED,
                    detail="Unable to resolve destination endpoint",
                    destination=destination,
                    endpoint="",
                    session=self._session,
                )
            else:
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
                env.sign(self.agent.identity)

                # Create awaitable future for MsgStatus and sync response
                fut = asyncio.Future()

                self._queue_envelope(env, endpoints, fut, sync)

                try:
                    result = await asyncio.wait_for(fut, timeout)
                except asyncio.TimeoutError:
                    log(
                        self.logger,
                        logging.ERROR,
                        "Timeout waiting for dispense response",
                    )
                    result = MsgStatus(
                        status=DeliveryStatus.FAILED,
                        detail="Timeout waiting for response",
                        destination=destination,
                        endpoint="",
                        session=self._session,
                    )

        if result.status == DeliveryStatus.DELIVERED and self._message_history:
            self._message_history.add_entry(
                EnvelopeHistoryEntry(
                    version=1,
                    sender=self.agent.address,
                    target=destination,
                    session=self._session,
                    schema_digest=message_schema_digest,
                    protocol_digest=protocol_digest,
                    payload=message_body,
                )
            )

        return result

    def _queue_envelope(
        self,
        envelope: Envelope,
        endpoints: list[str],
        response_future: asyncio.Future,
        sync: bool = False,
    ):
        """
        Queue an envelope for processing.

        Args:
            envelope (Envelope): The envelope to queue.
        """
        self._dispenser.add_envelope(envelope, endpoints, response_future, sync)

    async def send_and_receive(
        self,
        destination: str,
        message: Model,
        response_type: type[Model] | set[type[Model]],
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> tuple[Model | None, MsgStatus]:
        """
        Send a message to the specified destination and receive a response.

        Args:
            destination (str): The destination address to send the message to.
            message (Model): The message to be sent.
            response_type (type[Model] | set[type[Model]]): The type(s) of the response message.
            sync (bool): Whether to send the message synchronously or asynchronously.
            timeout (int): The timeout for sending the message, in seconds.

        Returns:
            tuple[Model | None, MsgStatus]: The response message if received and delivery status
        """
        schema_digest = Model.build_schema_digest(message)

        msg_status: MsgStatus = await self.send_raw(
            destination=destination,
            message_schema_digest=schema_digest,
            message_body=message.model_dump_json(),
            sync=sync,
            wait_for_response=True,
            timeout=timeout,
        )

        _, _, parsed_address = parse_identifier(destination)

        if msg_status.status != DeliveryStatus.DELIVERED:
            dispatcher.cancel_pending_response(
                self.agent.address, parsed_address, self._session
            )
            return None, msg_status

        response_msg: JsonStr | None = await dispatcher.wait_for_response(
            self.agent.address, parsed_address, self._session, timeout
        )

        if response_msg is None:
            log(self.logger, logging.ERROR, "Timeout waiting for response")
            return None, MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Timeout waiting for response",
                destination=destination,
                endpoint="",
                session=self._session,
            )

        response_types: set[type[Model]] = (
            {response_type} if isinstance(response_type, type) else response_type
        )

        response: Model | None = None
        for r_type in response_types:
            try:
                parsed: Model = r_type.parse_raw(response_msg)
                if parsed:
                    response = parsed
                    break
            except ValidationError:
                pass

        if response is None:
            log(
                logger=self.logger,
                level=logging.ERROR,
                message=f"Received unexpected response: {response_msg}",
            )
            msg_status = MsgStatus(
                status=DeliveryStatus.FAILED,
                detail="Received unexpected response type",
                destination=destination,
                endpoint="",
                session=self._session,
            )

        return response, msg_status

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
                logger=self.logger,
                level=logging.WARNING,
                message="Cannot send wallet message: no client available",
            )


class ExternalContext(InternalContext):
    """
    Represents the reactive context in which messages are handled and processed.

    Attributes:
        _message_received (MsgInfo): The received message.
        _queries (dict[str, asyncio.Future] | None): dictionary mapping query senders to their
            response Futures.
        _replies (dict[str, dict[str, type[Model]]] | None): Dictionary of allowed reply digests
            for each type of incoming message.
        _protocol (tuple[str, Protocol] | None): The supported protocol digest
            and the corresponding protocol.
    """

    def __init__(
        self,
        message_received: MsgInfo,
        queries: dict[str, asyncio.Future] | None = None,
        replies: dict[str, dict[str, type[Model]]] | None = None,
        protocol: tuple[str, "Protocol"] | None = None,
        **kwargs,
    ):
        """
        Initialize the ExternalContext instance and attributes needed from the InternalContext.

        Args:
            message_received (MsgInfo): Information about the received message.
            queries (dict[str, asyncio.Future]): Dictionary mapping query senders to their
                response Futures.
            replies (dict[str, dict[str, type[Model]]] | None): Dictionary of allowed replies
                for each type of incoming message.
            protocol (tuple[str, Protocol] | None): The optional tuple of protocols.
        """
        super().__init__(**kwargs)
        self._queries = queries or {}
        self._replies = replies
        self._message_received = message_received
        self._protocol = protocol or ("", None)

    def validate_replies(self, message_type: type[Model]) -> None:
        """
        If the context specifies replies, ensure that a valid reply was sent.

        Args:
            message_type (type[Model]): The type of the received message.
        """
        sender = self._message_received.sender
        received_digest = self._message_received.schema_digest

        # If no replies are defined, do not check for valid replies
        if not self._replies or received_digest not in self._replies:
            return

        # If replies are defined as empty, do not check for valid replies
        if self._replies[received_digest] == {}:
            return

        valid_replies = self._replies[received_digest] | {
            ERROR_MESSAGE_DIGEST: ErrorMessage
        }

        valid_reply_sent = False
        for target, msgs in self._outbound_messages.items():
            if target == sender and any(
                [digest in valid_replies for _, digest in msgs]
            ):
                valid_reply_sent = True
                break

        if not valid_reply_sent:
            valid_reply_types = {model.__name__ for model in valid_replies.values()}
            log(
                logger=self.logger,
                level=logging.ERROR,
                message=(
                    f"No valid reply {valid_reply_types} was sent to "
                    f"{sender} for received message: {message_type.__name__}."
                ),
            )

    async def send(
        self,
        destination: str,
        message: Model,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> MsgStatus:
        """
        Send a message to the specified destination.

        Args:
            destination (str): The destination address to send the message to.
            message (Model): The message to be sent.
            timeout (int | None): The optional timeout for sending the message, in seconds.

        Returns:
            MsgStatus: The delivery status of the message.
        """
        schema_digest = Model.build_schema_digest(message)

        # This is the re-active send method
        # at this point we have received a message and have built a context
        # replies, message_received, and protocol are set

        return await self.send_raw(
            destination=destination,
            message_schema_digest=schema_digest,
            message_body=message.model_dump_json(),
            timeout=timeout,
            protocol_digest=self._protocol[0],
            queries=self._queries,
        )


ContextFactory = Callable[[], Context]
