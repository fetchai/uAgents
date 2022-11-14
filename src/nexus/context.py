import uuid
from typing import Optional, Callable, Any, Awaitable

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
    ):
        self.storage = storage
        self._name = name
        self._address = str(address)
        self._resolver = resolve
        self._identity = identity

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

        # handle local dispatch of messages
        if dispatcher.contains(destination):
            await dispatcher.dispatch(
                self.address, destination, schema_digest, json_message
            )
            return

        # resolve the endpoint
        endpoint = await self._resolver.resolve(destination)
        if endpoint is None:
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

        # print(env.json())

        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint, headers={"content-type": "application/json"}, data=env.json()
            ) as _resp:
                pass
                # print(resp.status)
                # print(await resp.text())

        # attempt to resolve the address to send the message to
        # raise RuntimeError(f'Unable to resolve destination endpoint for address {destination}')
