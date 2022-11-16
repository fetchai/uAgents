from abc import ABC, abstractmethod
from typing import Dict, Optional

from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.client import LedgerClient, NetworkConfig

from nexus.crypto import Identity


CONTRACT_ALMANAC = "fetch1gfq09zhz5kzeue3k9whl8t6fv9ke8vkq6x4s8p6pj946t50dmc7qvw5npv"


def _query_record(wallet_address: str, service: str) -> dict:

    ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    contract = LedgerContract(None, ledger, CONTRACT_ALMANAC)
    query_msg = {"query_record": {"address": wallet_address, "record_type": service}}
    result = contract.query(query_msg)
    return result


class Resolver(ABC):
    @abstractmethod
    async def resolve(self, address: str) -> Optional[str]:
        pass


class AlmanacResolver(Resolver):
    async def resolve(self, address: str) -> str:
        wallet = LocalWallet(PrivateKey(Identity.get_key(address)))
        result = _query_record(wallet.address(), "Service")
        endpoint = result["record"]["record"]["Service"]["endpoints"][0]["url"]
        return endpoint


class RulesBasedResolver(Resolver):
    def __init__(self, rules: Dict[str, str]):
        self._rules = rules

    async def resolve(self, address: str) -> Optional[str]:
        return self._rules.get(address)
