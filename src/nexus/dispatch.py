from abc import ABC, abstractmethod
from typing import Set, Dict


class Sink(ABC):
    @abstractmethod
    async def handle_message(self, sender, message):
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

    async def dispatch(self, sender: str, destination: str, message):
        for destination in self._sinks.get(destination, set()):
            await destination.handle_message(sender, message)
