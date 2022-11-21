from abc import ABC, abstractmethod
from typing import Dict, Optional

from nexus.crypto import Identity
from nexus.network import get_ledger, get_reg_contract, get_wallet


def _query_record(wallet_address: str, service: str) -> dict:
    ledger = get_ledger("fetchai-testnet")
    contract = get_reg_contract(ledger)
    query_msg = {"query_record": {"address": wallet_address, "record_type": service}}
    result = contract.query(query_msg)
    return result


class Resolver(ABC):
    @abstractmethod
    async def resolve(self, address: str) -> Optional[str]:
        pass


class AlmanacResolver(Resolver):
    async def resolve(self, address: str) -> str:
        wallet = get_wallet(Identity.get_key(address))
        result = _query_record(wallet.address(), "Service")
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
