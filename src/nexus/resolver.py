from abc import ABC, abstractmethod
from typing import Dict, Optional

from nexus.crypto import Identity
from nexus.network import Network


def _query_record(wallet_address: str, service: str) -> dict:
    ledger = Network.get_ledger("fetchai-testnet")
    contract = Network.get_reg_contract(ledger)
    query_msg = {"query_record": {"address": wallet_address, "record_type": service}}
    result = contract.query(query_msg)
    return result


class Resolver(ABC):
    @abstractmethod
    async def resolve(self, address: str) -> Optional[str]:
        pass


class AlmanacResolver(Resolver):
    async def resolve(self, address: str) -> str:
        wallet = Network.get_wallet(Identity.get_key(address))
        result = _query_record(wallet.address(), "Service")
        endpoint = result["record"]["record"]["Service"]["endpoints"][0]["url"]
        return endpoint


class RulesBasedResolver(Resolver):
    def __init__(self, rules: Dict[str, str]):
        self._rules = rules

    async def resolve(self, address: str) -> Optional[str]:
        return self._rules.get(address)
