import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union

from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.client import (
    LedgerClient,
    NetworkConfig,
    DEFAULT_QUERY_INTERVAL_SECS,
    DEFAULT_QUERY_TIMEOUT_SECS,
)
from cosmpy.aerial.exceptions import NotFoundError, QueryTimeoutError
from cosmpy.aerial.contract.cosmwasm import create_cosmwasm_execute_msg
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.tx_helpers import TxResponse
from cosmpy.aerial.tx import Transaction

from uagents.config import (
    AgentNetwork,
    CONTRACT_ALMANAC,
    CONTRACT_SERVICE,
    AGENT_NETWORK,
    BLOCK_INTERVAL,
)


class AlmanacContract(LedgerContract):
    def is_registered(self, address: str) -> bool:
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            return False
        return True

    def get_expiry(self, address: str):
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            contract_state = self.query({"query_contract_state": {}})
            expiry = contract_state.get("state").get("expiry_height")
            return expiry * BLOCK_INTERVAL

        expiry = response.get("record")[0].get("expiry")
        height = response.get("height")

        return (expiry - height) * BLOCK_INTERVAL

    def get_endpoints(self, address: str):
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            return 0
        return response.get("record")[0]["record"]["service"]["endpoints"]

    def get_registration_msg(
        self,
        protocols: Dict,
        endpoints: Optional[Union[List[str], Dict[str, dict]]],
        signature: str,
        address: str,
    ) -> dict:
        return {
            "register": {
                "record": {
                    "service": {
                        "protocols": list(map(lambda x: x.digest, protocols.values())),
                        "endpoints": endpoints,
                    }
                },
                "signature": signature,
                "sequence": self.get_sequence(address),
                "agent_address": address,
            }
        }

    def get_sequence(self, address: str) -> int:
        query_msg = {"query_sequence": {"agent_address": address}}
        sequence = self.query(query_msg)["sequence"]

        return sequence


class ServiceContract(LedgerContract):
    def is_name_available(self, name: str):
        query_msg = {"domain_record": {"domain": f"{name}.agent"}}
        return self.query(query_msg)["is_available"]

    def is_owner(self, name: str, wallet_address: str):
        query_msg = {
            "permissions": {
                "domain": f"{name}.agent",
                "owner": {"address": {"address": wallet_address}},
            }
        }
        permission = self.query(query_msg)["permissions"]
        return permission == "admin"

    def _get_ownership_msg(self, name: str, wallet_address: str):
        return {
            "update_ownership": {
                "domain": f"{name}.agent",
                "owner": {"address": {"address": wallet_address}},
                "permissions": "admin",
            }
        }

    def _get_registration_msg(self, name: str, address: str):
        return {
            "register": {
                "domain": f"{name}.agent",
                "agent_address": address,
            }
        }

    def get_registration_tx(self, name: str, wallet_address: str, agent_address: str):
        if not self.is_name_available(name) and not self.is_owner(name, wallet_address):
            return None

        transaction = Transaction()

        ownership_msg = self._get_ownership_msg(name, wallet_address)
        registration_msg = self._get_registration_msg(name, agent_address)

        transaction.add_message(
            create_cosmwasm_execute_msg(wallet_address, CONTRACT_SERVICE, ownership_msg)
        )
        transaction.add_message(
            create_cosmwasm_execute_msg(
                wallet_address, CONTRACT_SERVICE, registration_msg
            )
        )

        return transaction


if AGENT_NETWORK == AgentNetwork.FETCHAI_TESTNET:
    _ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    _faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
elif AGENT_NETWORK == AgentNetwork.FETCHAI_MAINNET:
    _ledger = LedgerClient(NetworkConfig.fetchai_mainnet())
else:
    raise NotImplementedError


_almanac_contract = AlmanacContract(None, _ledger, CONTRACT_ALMANAC)
_service_contract = ServiceContract(None, _ledger, CONTRACT_SERVICE)


def get_ledger() -> LedgerClient:
    return _ledger


def get_faucet() -> FaucetApi:
    return _faucet_api


def get_almanac_contract() -> LedgerContract:
    return _almanac_contract


def get_service_contract() -> LedgerContract:
    return _service_contract


async def wait_for_tx_to_complete(
    tx_hash: str,
    timeout: Optional[timedelta] = None,
    poll_period: Optional[timedelta] = None,
) -> TxResponse:
    if timeout is None:
        timeout = timedelta(seconds=DEFAULT_QUERY_TIMEOUT_SECS)
    if poll_period is None:
        poll_period = timedelta(seconds=DEFAULT_QUERY_INTERVAL_SECS)
    start = datetime.now()
    while True:
        try:
            return _ledger.query_tx(tx_hash)
        except NotFoundError:
            pass

        delta = datetime.now() - start
        if delta >= timeout:
            raise QueryTimeoutError()

        await asyncio.sleep(poll_period.total_seconds())
