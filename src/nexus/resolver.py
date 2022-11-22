from abc import ABC, abstractmethod
from typing import Dict, Optional

from nexus.network import get_reg_contract


def _query_record(agent_address: str, service: str) -> dict:
    contract = get_reg_contract()
    query_msg = {"query_record": {"address": agent_address, "record_type": service}}
    result = contract.query(query_msg)
    return result


class Resolver(ABC):
    @abstractmethod
    async def resolve(self, address: str) -> Optional[str]:
        pass


class AlmanacResolver(Resolver):
    async def resolve(self, address: str) -> str:
        result = _query_record(address, "Service")
        if result is not None:
            record = result.get("record") or {}
            endpoints = record.get("record", {}).get("Service", {}).get("endpoints", [])

            # For now just use the first endpoint
            if len(endpoints) > 0:
                return endpoints[0].get("url")
        return None


class RulesBasedResolver(Resolver):
    def __init__(self, rules: Dict[str, str]):
        self._rules = rules

    async def resolve(self, address: str) -> Optional[str]:
        return self._rules.get(address)
