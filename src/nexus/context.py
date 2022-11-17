import uuid
from typing import Dict, Set, Optional, Callable, Any, Awaitable

import aiohttp

from nexus.crypto import Identity
from nexus.dispatch import dispatcher
from nexus.envelope import Envelope
from nexus.models import Model
from nexus.resolver import Resolver
from nexus.storage import KeyValueStore

IntervalCallback = Callable[["Context"], Awaitable[None]]
MessageCallback = Callable[["Context", str, Any], Awaitable[None]]


class Context:
    def __init__(
        self,
        address: str,
        name: Optional[str],
        storage: KeyValueStore,
        resolve: Resolver,
        identity: Identity,
        inbox: Dict[str, str],
        replies: Dict[str, Set[str]],
    ):
        self.storage = storage
        self._name = name
        self._address = str(address)
        self._resolver = resolve
        self._identity = identity
        self._inbox = inbox
        self._replies = replies

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
        if destination in self._inbox:
            received = self._inbox[destination]
            # ensure the reply is valid
            if schema_digest not in self._replies[received["digest"]]:
                raise RuntimeError(
                    f"Outgoing message {message} is not a valid reply to {received['msg']}"
                )

        # handle local dispatch of messages
        if dispatcher.contains(destination):
            await dispatcher.dispatch(
                self.address, destination, schema_digest, json_message
            )
            return

        # resolve the endpoint
        endpoint = await self._resolver.resolve(destination)
        if endpoint is None:
            raise RuntimeError(
                f"Unable to resolve destination endpoint for address {destination}"
            )

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
            raise RuntimeError(f"Unable to send envelope to {destination} @ {endpoint}")
