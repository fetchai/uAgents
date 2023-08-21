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
    message: Any
    schema_digest: str


ERROR_MESSAGE_DIGEST = Model.build_schema_digest(ErrorMessage)


class Context:
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
        self.storage = storage
        self.wallet = wallet
        self.ledger = ledger
        self._name = name
        self._address = str(address)
        self._resolver = resolve
        self._identity = identity
        self._queries = queries
        self._session = session or uuid.uuid4()
        self._replies = replies
        self._interval_messages = interval_messages
        self._message_received = message_received
        self._protocols = protocols or {}
        self._logger = logger

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        return self._address[:10]

    @property
    def address(self) -> str:
        return self._address

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def protocols(self) -> Optional[Dict[str, Protocol]]:
        return self._protocols

    @property
    def session(self) -> uuid.UUID:
        return self._session

    def get_message_protocol(self, message_schema_digest) -> Optional[str]:
        for protocol_digest, protocol in self._protocols.items():
            for reply_models in protocol.replies.values():
                if message_schema_digest in reply_models:
                    return protocol_digest
        return None

    def get_agents_by_protocol(
        self, protocol_digest: str, limit: Optional[int] = None
    ) -> List[str]:
        if not isinstance(
            protocol_digest, str
        ) or not protocol_digest.startswith("proto:"):
            self.logger.error(f"Invalid protocol digest: {protocol_digest}")
            raise ValueError("Invalid protocol digest")
        response = requests.post(
            url=ALMANAC_API_URL + "search",
            json={"text": protocol_digest[6:]},
            timeout=DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            data = response.json()
            agents = [
                agent["address"]
                for agent in data
                if agent["status"] == "local"
            ]
            return agents[:limit]
        return []

    async def send(
        self,
        destination: str,
        message: Model,
        timeout: Optional[int] = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ):
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
        agents = self.get_agents_by_protocol(destination_protocol, limit=limit)
        if not agents:
            self.logger.error(
                f"No active agents found for: {destination_protocol}"
            )
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
        # check if this message is a reply
        if (
            self._message_received is not None
            and self._replies
            and schema_digest != ERROR_MESSAGE_DIGEST
        ):
            received = self._message_received
            if received.schema_digest in self._replies:
                # ensure the reply is valid
                if schema_digest not in self._replies[received.schema_digest]:
                    self._logger.exception(
                        f"Outgoing message {message_type or ''} "
                        f"is not a valid reply to {received.message}"
                    )
                    return

        # check if this message is a valid interval message
        if self._message_received is None and self._interval_messages:
            if schema_digest not in self._interval_messages:
                self._logger.exception(
                    f"Outgoing message {message_type} is not a valid interval message"
                )
                return

        # handle local dispatch of messages
        if dispatcher.contains(destination):
            await dispatcher.dispatch(
                self.address, destination, schema_digest, json_message, self._session
            )
            return

        # handle queries waiting for a response
        if destination in self._queries:
            self._queries[destination].set_result((json_message, schema_digest))
            del self._queries[destination]
            return

        # resolve the endpoint
        destination_address, endpoint = await self._resolver.resolve(destination)
        if endpoint is None:
            self._logger.exception(
                f"Unable to resolve destination endpoint for address {destination}"
            )
            return

        # calculate when envelope expires
        expires = int(time()) + timeout

        # handle external dispatch of messages
        env = Envelope(
            version=1,
            sender=self.address,
            target=destination_address,
            session=self._session,
            schema_digest=schema_digest,
            protocol_digest=self.get_message_protocol(schema_digest),
            expires=expires,
        )
        env.encode_payload(json_message)
        env.sign(self._identity)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint, headers={"content-type": "application/json"}, data=env.json()
            ) as resp:
                success = resp.status == 200

        if not success:
            self._logger.exception(
                f"Unable to send envelope to {destination_address} @ {endpoint}"
            )
