# Registration

Agent registration in the almanac-contract is a key part for remote agents communication.

To be found by other μAgents, each μAgent needs to register (paying a small fee) in the almanac contract using their [agent address](addresses.md). Therefore, your agents need to have funds available in their [Fetch address](addresses.md). When using the testnet, you can use the function `fund_agent_if_low` to fund your agent:

```python
from uagents.setup import fund_agent_if_low
from uagents import Agent

agent = Agent(name="alice", seed="agent1 secret phrase")

fund_agent_if_low(agent.wallet.address())
```
This function will check if you have enough tokens to register in the `almanac-contract`. If not it will add tokens to your [Fetch address](addresses.md). Make sure to add a `seed` to your agent so you don't have to fund different addresses each time you run your agent.

μAgents can communicate by querying the `almanac-contract` and retrieving an HTTP endpoint from the recipient μAgent. Therefore, we need to specify the [service endpoints](almanac-endpoint.md) when defining an agent:

```python
agent = Agent(
    name="alice",
    port=8000,
    seed="agent1 secret phrase",
    endpoint=["http://127.0.0.1:8000/submit"],
)
```

Here we defined a local http address, but you could also define a remote address to allow agent communication over different machines through the internet.