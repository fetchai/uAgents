import asyncio
from abc import ABC, abstractmethod
from asyncio import Future
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from uagents_core.models import Model

from uagents.types import JsonStr, MsgInfo, RestMethod

PendingResponseKey = tuple[str, str, UUID]


@dataclass
class PendingResponse:
    future: Future[MsgInfo]
    expected_schema_digests: set[str] | None = None

    def accepts(self, schema_digest: str) -> bool:
        """Whether an incoming message should resolve this response slot."""
        if self.future.done():
            return False
        if self.expected_schema_digests is None:
            return True
        return schema_digest in self.expected_schema_digests


class Sink(ABC):
    """
    Abstract base class for sinks that handle messages.
    """

    @abstractmethod
    async def handle_message(
        self, sender: str, schema_digest: str, message: JsonStr, session: UUID
    ):
        raise NotImplementedError

    @abstractmethod
    async def handle_rest(
        self, method: RestMethod, endpoint: str, message: Model | None
    ):
        raise NotImplementedError


class Dispatcher:
    """
    Dispatches incoming messages to internal sinks.
    """

    def __init__(self):
        self._sinks: dict[str, set[Sink]] = {}
        self._pending_responses: dict[PendingResponseKey, PendingResponse] = {}

    @property
    def sinks(self) -> dict[str, set[Sink]]:
        return self._sinks

    @property
    def pending_responses(self) -> dict[PendingResponseKey, PendingResponse]:
        return self._pending_responses

    async def register_pending_response(
        self,
        sender: str,
        destination: str,
        session: UUID,
        expected_schema_digests: set[str] | None = None,
    ):
        loop = asyncio.get_running_loop()
        self._pending_responses[(sender, destination, session)] = PendingResponse(
            future=loop.create_future(),
            expected_schema_digests=expected_schema_digests,
        )

    def cancel_pending_response(self, sender: str, destination: str, session: UUID):
        key: tuple[str, str, UUID] = (sender, destination, session)
        if key in self._pending_responses:
            del self._pending_responses[key]

    async def wait_for_response(
        self, sender: str, destination: str, session: UUID, timeout: float
    ) -> MsgInfo | None:
        key: tuple[str, str, UUID] = (sender, destination, session)
        try:
            response = await asyncio.wait_for(
                self._pending_responses[key].future, timeout
            )
        except asyncio.TimeoutError:
            response = None
        except KeyError:
            # Key was removed before wait_for completed
            response = None
        finally:
            # Safe deletion - only delete if key exists
            self._pending_responses.pop(key, None)
        return response

    def dispatch_pending_response(
        self,
        sender: str,
        destination: str,
        session: UUID,
        schema_digest: str,
        message: JsonStr,
    ) -> bool:
        key = (destination, sender, session)
        pending = self._pending_responses.get(key)
        if pending is not None and pending.accepts(schema_digest):
            pending.future.set_result(
                MsgInfo(message=message, sender=sender, schema_digest=schema_digest)
            )
            return True
        return False

    def register(self, address: str, sink: Sink):
        destinations = self._sinks.get(address, set())
        destinations.add(sink)
        self._sinks[address] = destinations

    def unregister(self, address: str, sink: Sink):
        destinations = self._sinks.get(address, set())
        destinations.discard(sink)
        if len(destinations) == 0:
            del self._sinks[address]
            return
        self._sinks[address] = destinations

    def contains(self, address: str) -> bool:
        return address in self._sinks

    async def dispatch_msg(
        self,
        sender: str,
        destination: str,
        schema_digest: str,
        message: JsonStr,
        session: UUID,
    ) -> None:
        if self.dispatch_pending_response(
            sender, destination, session, schema_digest, message
        ):
            return
        for handler in self._sinks.get(destination, set()):
            await handler.handle_message(sender, schema_digest, message, session)

    async def dispatch_rest(
        self,
        destination: str,
        method: RestMethod,
        endpoint: str,
        message: Model | None,
    ) -> dict[str, Any] | Model | None:
        for handler in self._sinks.get(destination, set()):
            return await handler.handle_rest(method, endpoint, message)


dispatcher = Dispatcher()
