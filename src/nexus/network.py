from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.client import LedgerClient, NetworkConfig


CONTRACT_ALMANAC = "fetch1gfq09zhz5kzeue3k9whl8t6fv9ke8vkq6x4s8p6pj946t50dmc7qvw5npv"


def get_ledger(network: str) -> LedgerClient:
    if network == "fetchai-testnet":
        ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    elif network == "fetchai-mainnet":
        ledger = LedgerClient(NetworkConfig.fetchai_mainnet())
    else:
        raise Exception(f"Network {network} not recognized")
    return ledger


def get_reg_contract(ledger: LedgerClient) -> LedgerContract:
    contract = LedgerContract(None, ledger, CONTRACT_ALMANAC)
    return contract


def get_wallet(key: str) -> LocalWallet:
    wallet = LocalWallet(PrivateKey(key))
    return wallet
