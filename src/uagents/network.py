import asyncio
from datetime import datetime, timedelta
from typing import Optional

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
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.tx import SigningCfg, Transaction
from cosmpy.aerial.tx_helpers import TxResponse
from cosmpy.aerial.wallet import Wallet

from uagents.config import Network, CONTRACT_ALMANAC, AGENT_NETWORK


if AGENT_NETWORK == Network.FETCHAI_TESTNET:
    _ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    _faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
elif AGENT_NETWORK == Network.FETCHAI_MAINNET:
    _ledger = LedgerClient(NetworkConfig.fetchai_mainnet())
else:
    raise NotImplementedError


_contract = LedgerContract(None, _ledger, CONTRACT_ALMANAC)


def get_ledger() -> LedgerClient:
    return _ledger


def get_faucet() -> FaucetApi:
    return _faucet_api


def get_reg_contract() -> LedgerContract:
    return _contract


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
