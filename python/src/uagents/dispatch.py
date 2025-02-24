import asyncio
import uuid
from abc import ABC, abstractmethod
from asyncio import Future
from typing import Any, Dict, Optional, Set, Tuple, Union

from uagents.models import Model
from uagents.types import JsonStr, RestMethod

PendingResponseKey = Tuple[str, str, uuid.UUID]


class Sink(ABC):
    """
    Abstract base class for sinks that handle messages.
    """

    @abstractmethod
    async def handle_message(
        self, sender: str, schema_digest: str, message: JsonStr, session: uuid.UUID
    ):
        pass

    @abstractmethod
    async def handle_rest(
        self, method: RestMethod, endpoint: str, message: Optional[Model]
    ):
        pass


class Dispatcher:
    """
    Dispatches incoming messages to internal sinks.
    """

    def __init__(self):
        self._sinks: Dict[str, Set[Sink]] = {}
        self._pending_responses: Dict[PendingResponseKey, Future[JsonStr]] = {}

    @property
    def sinks(self) -> Dict[str, Set[Sink]]:
        return self._sinks

    @property
    def pending_responses(self) -> Dict[PendingResponseKey, Future[JsonStr]]:
        return self._pending_responses

    def register_pending_response(
        self, sender: str, destination: str, session: uuid.UUID
    ):
        self._pending_responses[(sender, destination, session)] = (
            asyncio.get_event_loop().create_future()
        )

    async def wait_for_response(
        self, sender: str, destination: str, session: uuid.UUID, timeout: float
    ) -> Optional[JsonStr]:
        key = (sender, destination, session)
        try:
            response = await asyncio.wait_for(self._pending_responses[key], timeout)
        except asyncio.TimeoutError:
            response = None
        del self._pending_responses[key]
        return response

    def dispatch_pending_response(
        self, sender: str, destination: str, session: uuid.UUID, message: JsonStr
    ) -> bool:
        key = (destination, sender, session)
        if key in self._pending_responses:
            self._pending_responses[key].set_result(message)
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
        session: uuid.UUID,
    ) -> None:
        if self.dispatch_pending_response(sender, destination, session, message):
            return
        for handler in self._sinks.get(destination, set()):
            await handler.handle_message(sender, schema_digest, message, session)

    async def dispatch_rest(
        self,
        destination: str,
        method: RestMethod,
        endpoint: str,
        message: Optional[Model],
    ) -> Optional[Union[Dict[str, Any], Model]]:
        for handler in self._sinks.get(destination, set()):
            return await handler.handle_rest(method, endpoint, message)


dispatcher = Dispatcher()
