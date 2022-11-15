from cosmpy.aerial.client import NetworkConfig
from cosmpy.aerial.faucet import FaucetApi
from nexus import Agent


alice = Agent(name="alice", seed="alice recovery password", network="fetchai-testnet")
bob = Agent(name="bob", seed="bob recovery password", network="fetchai-testnet")

# Network configuration
ledger = alice.ledger
faucet_api = FaucetApi(NetworkConfig.latest_stable_testnet())

alice_balance = ledger.query_bank_balance(alice.wallet.address())
bob_balance = ledger.query_bank_balance(bob.wallet.address())

if alice_balance == 0:
    # Add tokens to alice's wallet
    faucet_api.get_wealth(alice.wallet.address())

if bob_balance == 0:
    # Add tokens to bob's wallet
    faucet_api.get_wealth(bob.wallet.address())


bob.register(protocols=["foo"], endpoints=["bar"])
alice.register(protocols=["foo"], endpoints=["bar"])

# query all records for a given address
print(bob.query_records(alice.wallet.address()))

# query specified record for a given address
print(bob.query_record(alice.wallet.address(), "Service"))
