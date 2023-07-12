import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union

from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.client import (
    Account,
    LedgerClient,
    NetworkConfig,
    DEFAULT_QUERY_INTERVAL_SECS,
    DEFAULT_QUERY_TIMEOUT_SECS,
    create_bank_send_msg,
)
from cosmpy.aerial.exceptions import NotFoundError, QueryTimeoutError
from cosmpy.aerial.contract.cosmwasm import create_cosmwasm_execute_msg
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.tx import SigningCfg, Transaction
from cosmpy.aerial.tx_helpers import TxResponse
from cosmpy.aerial.wallet import Wallet

from uagents.config import (
    AgentNetwork,
    CONTRACT_ALMANAC,
    CONTRACT_NAME_SERVICE,
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


class NameServiceContract(LedgerContract):
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

        registration_msg = self._get_registration_msg(name, agent_address)

        transaction.add_message(
            create_cosmwasm_execute_msg(
                wallet_address, CONTRACT_NAME_SERVICE, registration_msg
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
_name_service_contract = NameServiceContract(None, _ledger, CONTRACT_NAME_SERVICE)


def get_ledger() -> LedgerClient:
    return _ledger


def get_faucet() -> FaucetApi:
    return _faucet_api


def get_almanac_contract() -> LedgerContract:
    return _almanac_contract


def get_service_contract() -> LedgerContract:
    return _name_service_contract


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


def create_send_tokens_transaction(
    sender: Wallet, destination: str, amount: int, denom: str, **kwargs
):
    transaction = Transaction()
    transaction.add_message(
        create_bank_send_msg(sender.address(), destination, amount, denom)
    )
    return prepare_basic_transaction(_ledger, transaction, sender, **kwargs)


def prepare_basic_transaction(
    client: LedgerClient,
    transaction: Transaction,
    sender: Wallet,
    account: Optional[Account] = None,
    gas_limit: Optional[int] = None,
    memo: Optional[str] = None,
) -> Transaction:
    if account is None:
        account = client.query_account(sender.address())

    if gas_limit is not None:
        fee = client.estimate_fee_from_gas(gas_limit)
    else:
        transaction.seal(
            SigningCfg.direct(sender.public_key(), account.sequence),
            fee="",
            gas_limit=0,
            memo=memo,
        )
        transaction.sign(
            sender.signer(), client.network_config.chain_id, account.number
        )
        transaction.complete()

        # simulate the gas and fee for the transaction
        gas_limit, fee = client.estimate_gas_and_fee_for_tx(transaction)

    # finally, build the final transaction that will be executed with the correct gas and fee values
    transaction.seal(
        SigningCfg.direct(sender.public_key(), account.sequence),
        fee=fee,
        gas_limit=gas_limit,
        memo=memo,
    )

    return transaction
