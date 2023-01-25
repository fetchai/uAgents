# Agent addresses

You can print your agent's addresses in the following way:

```python
from uagents import Agent

alice = Agent(name="alice")

print("uAgent address: ", alice.address)
print("Fetch network address: ", alice.wallet.address())
```

Your agent will have two types of addresses:

- `uAgent address:` represents the main uAgent identifier. Other uAgents can use this to query the agent's information in the almanac-contract.

- `Fetch address:` provides the agent with the capabilities for interacting with the fetch ledger such as registering in the almanac-contract.