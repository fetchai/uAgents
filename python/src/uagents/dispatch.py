from abc import ABC, abstractmethod
from typing import Dict, Set
import uuid

JsonStr = str


class Sink(ABC):
    """
    Abstract base class for sinks that handle messages.
    """

    @abstractmethod
    async def handle_message(
        self, sender: str, schema_digest: str, message: JsonStr, session: uuid.UUID
    ):
        pass


class Dispatcher:
    """
    Dispatches messages to sinks.
    """

    def __init__(self):
        self._sinks: Dict[str, Set[Sink]] = {}

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

    async def dispatch(
        self,
        sender: str,
        destination: str,
        schema_digest: str,
        message: JsonStr,
        session: uuid.UUID,
    ):
        for handler in self._sinks.get(destination, set()):
            await handler.handle_message(sender, schema_digest, message, session)


dispatcher = Dispatcher()
