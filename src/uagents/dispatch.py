from abc import ABC, abstractmethod
from typing import Dict, Set

JsonStr = str


class Sink(ABC):
    @abstractmethod
    async def handle_message(self, sender: str, schema_digest: str, message: JsonStr):
        pass


class Dispatcher:
    def __init__(self):
        self._sinks: Dict[str, Set[Sink]] = {}

    def register(self, address: str, sink: Sink):
        destinations = self._sinks.get(address, set())
        destinations.add(sink)
        self._sinks[address] = destinations

    def unregister(self, address: str, sink: Sink):
        destinations = self._sinks.get(address, set())
        destinations.discard(sink)
        self._sinks[address] = destinations

    def contains(self, address: str) -> bool:
        return address in self._sinks

    async def dispatch(
        self, sender: str, destination: str, schema_digest: str, message: JsonStr
    ):
        for handler in self._sinks.get(destination, set()):
            await handler.handle_message(sender, schema_digest, message)


dispatcher = Dispatcher()
