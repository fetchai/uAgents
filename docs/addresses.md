# Agent addresses

You can print your agent's addresses in the following way:

```python
from uagents import Agent
alice = Agent(name="alice")

print("uAgent address: ",alice.address)
print("Fetch network address: ",alice.wallet.address())
```

Your agent will have two types of addresses:

- `Agent address:` represents the main uAgent identifier, other uAgents will need this to query the agent's information in the almanac-contract.

- `Fetch address:` provides the agent with the capabilities for interacting with the fetch ledger such as registering in the almanac-contract. You will need to add funds to it in order to interact with the fetch ledger, you can add funds to it depending on the network your uAgent is interacting with. Please visit [Faucet](https://docs.fetch.ai/ledger_v2/faucet/) for more information.

It is useful to include a `seed` parameter when creating an agent to set fixed addresses. Otherwise, random addresses will be generated every time you run agent alice.

```python
alice = Agent(name="alice", seed="alice recovery phrase")
```