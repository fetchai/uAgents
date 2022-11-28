
Micro Agents (uAgents) emerge as an additional way to lower the learning curve for users to get into the [AEA Framework](https://docs.fetch.ai/aea/)

# Getting Started

## Install from source

Download the latest released version from github and navigate to the uAgents directory

```
git clone https://github.com/fetchai/uAgents.git
cd uAgents
```

Isntall the required dependencies

```
poetry install
```

Open the virtual environment

```
poetry shell
```

## Registration

- Each uAgent needs to register in a smart contract almanac in order to be found by other uAgents.
- To register, an uAgent provides its address along with metadata about the service endpoints that it provides.
- They have to pay a small fee for this registration.
- In order to keep the registration information up to date, the agent will need to continually re-register their information.
- Each individual uAgent can query the current active registrations for information to communicate with other agents.
- uAgents can communicate by retrieving an HTTP endpoint from the recipient uAgent.


## Create an uAgent

You can create your first uAgent by running the following python script

```python
from nexus import Agent
agent = Agent(name="alice")

print("uAgent address: ",agent.address)
print("uAgent fetch address: ",agent.wallet.address())
```

Your agent will have two types of addresses:
- `Agent address:` represents the main uAgent identifier, other uAgents will need this to query the contract almanac.
- `Fetch address:` provides the agent with the capabilities for interacting with the fetch ledger such as registering in the contract almanac. You will need to add funds to it in order to interact with the fetch ledger, you can add funds to it depending on the network your uAgent is interacting with. Please visit [Faucet](https://docs.fetch.ai/ledger_v2/faucet/) for more information.
