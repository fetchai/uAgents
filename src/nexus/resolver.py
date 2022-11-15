from abc import ABC, abstractmethod
from typing import Dict, Optional


class Resolver(ABC):
    @abstractmethod
    async def resolve(self, address: str) -> Optional[str]:
        pass


class AlmanacResolver(Resolver):
    async def resolve(self, address: str) -> str:
        # this would be the place where a call to the agent almanac sits
        raise RuntimeError("Not implemented")


class RulesBasedResolver(Resolver):
    def __init__(self, rules: Dict[str, str]):
        self._rules = rules

    async def resolve(self, address: str) -> Optional[str]:
        return self._rules.get(address)
