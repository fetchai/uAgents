import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Dict, Set, Optional, Callable, Any, Awaitable

import aiohttp
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet

from nexus.crypto import Identity
from nexus.dispatch import dispatcher
from nexus.envelope import Envelope
from nexus.models import Model
from nexus.resolver import Resolver
from nexus.storage import KeyValueStore

IntervalCallback = Callable[["Context"], Awaitable[None]]
MessageCallback = Callable[["Context", str, Any], Awaitable[None]]


@dataclass
class MsgDigest:
    message: Any
    schema_digest: str


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
        replies: Optional[Dict[str, Set[str]]] = None,
        interval_messages: Optional[Dict[str, Set[str]]] = None,
        message_received: Optional[MsgDigest] = None,
    ):
        self.storage = storage
        self.wallet = wallet
        self.ledger = ledger
        self._name = name
        self._address = str(address)
        self._resolver = resolve
        self._identity = identity
        self._queries = queries
        self._replies = replies
        self._interval_messages = interval_messages
        self._message_received = message_received

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        return self._address[:10]

    @property
    def address(self) -> str:
        return self._address

    async def send(self, destination: str, message: Model):
        # convert the message into object form
        json_message = message.json()
        schema_digest = Model.build_schema_digest(message)

        # check if this message is a reply
        if self._message_received is not None and self._replies:
            received = self._message_received
            if received.schema_digest in self._replies:
                # ensure the reply is valid
                if schema_digest not in self._replies[received.schema_digest]:
                    logging.exception(
                        f"Outgoing message {type(message)} "
                        f"is not a valid reply to {received.message}"
                    )
                    return

        # check if this message is a valid interval message
        if self._message_received is None and self._interval_messages:
            if schema_digest not in self._interval_messages:
                logging.exception(
                    f"Outgoing message {type(message)} is not a valid interval message"
                )
                return

        # handle local dispatch of messages
        if dispatcher.contains(destination):
            await dispatcher.dispatch(
                self.address, destination, schema_digest, json_message
            )
            return

        # handle queries waiting for a response
        if destination[:4] == "user":
            if destination not in self._queries:
                logging.exception(f"Unable to resolve query to user {destination}")
                return
            self._queries[destination].set_result(message)
            del self._queries[destination]
            return

        # resolve the endpoint
        endpoint = await self._resolver.resolve(destination)
        if endpoint is None:
            logging.exception(
                f"Unable to resolve destination endpoint for address {destination}"
            )
            return

        # handle external dispatch of messages
        env = Envelope(
            version=1,
            sender=self.address,
            target=destination,
            session=uuid.uuid4(),
            protocol=schema_digest,
        )
        env.encode_payload(json_message)
        env.sign(self._identity)

        success = False
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint, headers={"content-type": "application/json"}, data=env.json()
            ) as resp:
                success = resp.status == 200

        if not success:
            logging.exception(f"Unable to send envelope to {destination} @ {endpoint}")
