from cosmpy.aerial.client import NetworkConfig
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.client import LedgerClient
from nexus import Agent


alice = Agent(name="alice", seed="alice recovery password")
bob = Agent(name="bob", seed="bob recovery password")

# Network configuration
ledger = LedgerClient(NetworkConfig.latest_stable_testnet())

alice_balance = ledger.query_bank_balance(alice.wallet.address())
bob_balance = ledger.query_bank_balance(bob.wallet.address())

if alice_balance == 0:
    # Add tokens to alice's wallet
    faucet_api = FaucetApi(NetworkConfig.latest_stable_testnet())
    faucet_api.get_wealth(alice.wallet.address())

if bob_balance == 0:
    # Add tokens to bob's wallet
    faucet_api = FaucetApi(NetworkConfig.latest_stable_testnet())
    faucet_api.get_wealth(bob.wallet.address())


bob.register(protocols=["foo"], endpoints=["bar"])
alice.register(protocols=["foo"], endpoints=["bar"])

print(bob.query_registration(alice.wallet.address()))
