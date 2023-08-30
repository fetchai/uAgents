import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List

from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.client import (
    Account,
    LedgerClient,
    NetworkConfig,
    DEFAULT_QUERY_INTERVAL_SECS,
    DEFAULT_QUERY_TIMEOUT_SECS,
    create_bank_send_msg,
    prepare_and_broadcast_basic_transaction,
)
from cosmpy.aerial.exceptions import NotFoundError, QueryTimeoutError
from cosmpy.aerial.contract.cosmwasm import create_cosmwasm_execute_msg
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.tx import SigningCfg, Transaction
from cosmpy.aerial.tx_helpers import TxResponse
from cosmpy.aerial.wallet import Wallet, LocalWallet

from uagents.config import (
    AgentNetwork,
    CONTRACT_ALMANAC,
    CONTRACT_NAME_SERVICE,
    AGENT_NETWORK,
    AVERAGE_BLOCK_INTERVAL,
    REGISTRATION_FEE,
    REGISTRATION_DENOM,
    get_logger,
)


logger = get_logger("network")

if AGENT_NETWORK == AgentNetwork.FETCHAI_TESTNET:
    _ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    _faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
elif AGENT_NETWORK == AgentNetwork.FETCHAI_MAINNET:
    _ledger = LedgerClient(NetworkConfig.fetchai_mainnet())
else:
    raise NotImplementedError


def get_ledger() -> LedgerClient:
    return _ledger


def get_faucet() -> FaucetApi:
    return _faucet_api


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


class AlmanacContract(LedgerContract):
    def is_registered(self, address: str) -> bool:
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            return False
        return True

    def get_expiry(self, address: str) -> int:
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            contract_state = self.query({"query_contract_state": {}})
            expiry = contract_state.get("state").get("expiry_height")
            return expiry * AVERAGE_BLOCK_INTERVAL

        expiry = response.get("record")[0].get("expiry")
        height = response.get("height")

        return (expiry - height) * AVERAGE_BLOCK_INTERVAL

    def get_endpoints(self, address: str):
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            return None
        return response.get("record")[0]["record"]["service"]["endpoints"]

    def get_protocols(self, address: str):
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            return None
        return response.get("record")[0]["record"]["service"]["protocols"]

    async def register(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        agent_address: str,
        protocols: List[str],
        endpoints: List[Dict[str, Any]],
        signature: str,
    ):
        transaction = Transaction()

        almanac_msg = {
            "register": {
                "record": {
                    "service": {
                        "protocols": protocols,
                        "endpoints": endpoints,
                    }
                },
                "signature": signature,
                "sequence": self.get_sequence(agent_address),
                "agent_address": agent_address,
            }
        }

        transaction.add_message(
            create_cosmwasm_execute_msg(
                wallet.address(),
                self.address,
                almanac_msg,
                funds=f"{REGISTRATION_FEE}{REGISTRATION_DENOM}",
            )
        )

        transaction = prepare_and_broadcast_basic_transaction(
            ledger, transaction, wallet
        )
        await wait_for_tx_to_complete(transaction.tx_hash)

    def get_sequence(self, address: str) -> int:
        query_msg = {"query_sequence": {"agent_address": address}}
        sequence = self.query(query_msg)["sequence"]

        return sequence


_almanac_contract = AlmanacContract(None, _ledger, CONTRACT_ALMANAC)


def get_almanac_contract() -> AlmanacContract:
    return _almanac_contract


class NameServiceContract(LedgerContract):
    def is_name_available(self, name: str, domain: str):
        query_msg = {"domain_record": {"domain": f"{name}.{domain}"}}
        return self.query(query_msg)["is_available"]

    def is_owner(self, name: str, domain: str, wallet_address: str):
        query_msg = {
            "permissions": {
                "domain": f"{name}.{domain}",
                "owner": {"address": {"address": wallet_address}},
            }
        }
        permission = self.query(query_msg)["permissions"]
        return permission == "admin"

    def is_domain_public(self, domain: str):
        res = self.query({"domain_record": {"domain": f".{domain}"}})
        return res["is_public"]

    def get_registration_tx(
        self, name: str, wallet_address: str, agent_address: str, domain: str
    ):
        if not self.is_name_available(name, domain) and not self.is_owner(
            name, domain, wallet_address
        ):
            return None

        registration_msg = {
            "register": {
                "domain": f"{name}.{domain}",
                "agent_address": agent_address,
            }
        }

        transaction = Transaction()
        transaction.add_message(
            create_cosmwasm_execute_msg(
                wallet_address, CONTRACT_NAME_SERVICE, registration_msg
            )
        )

        return transaction

    async def register(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        agent_address: str,
        name: str,
        domain: str,
    ):
        logger.info("Registering name...")

        if not get_almanac_contract().is_registered(agent_address):
            logger.warning(
                f"Agent {name} needs to be registered in almanac contract to register its name"
            )
            return

        if not self.is_domain_public(domain):
            logger.warning(
                f"Domain {domain} is not public, please select a public domain"
            )
            return

        transaction = self.get_registration_tx(
            name, str(wallet.address()), agent_address, domain
        )

        if transaction is None:
            logger.error(
                f"Please select another name, {name} is owned by another address"
            )
            return
        transaction = prepare_and_broadcast_basic_transaction(
            ledger, transaction, wallet
        )
        await wait_for_tx_to_complete(transaction.tx_hash)
        logger.info("Registering name...complete")


_name_service_contract = NameServiceContract(None, _ledger, CONTRACT_NAME_SERVICE)


def get_name_service_contract() -> NameServiceContract:
    return _name_service_contract
