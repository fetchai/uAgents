
# Introduction
uAgents is a fast and lightweight framework that makes it easy to build agents for a variety of decentralized use cases

# Getting Started

!!! Info "System requirements"
    uAgents can be used on `Ubuntu/Debian` and `MacOS`.
    
    You need <a href="https://www.python.org/downloads/" target="_blank">Python</a> 3.8, 3.9 or 3.10 on your system.

## Install from source

Download the latest released version from github and navigate to the uAgents directory

```
git clone https://github.com/fetchai/uAgents.git
cd uAgents
```

Install the required dependencies

```
poetry install
```

Open the virtual environment

```
poetry shell
```

## Create an agent

You can create your first uAgent by running the following python script

```python
from nexus import Agent
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

## Add an interval task

We can use the `on_interval` decorator to repeat a task in a specified period.
We also need to import `Context` to have access to the information that the agent needs to function.
In this case, we will just define a `say_hello` function that will print out the agent name every 2 seconds.
```python
from nexus import Context

@alice.on_interval(period=2.0)
async def say_hello(ctx: Context):
    print(f'hello, my name is {ctx.name}')

```

## Run agent

We can now put together what we learned above and run our agent! When running an agent it will run an http server. 

```python
from nexus import Agent, Context

alice = Agent(name="alice", seed="alice recovery phrase")

print("uAgent address: ",alice.address)
print("Fetch network address: ",alice.wallet.address())

@alice.on_interval(period=2.0)
async def say_hello(ctx: Context):
    print(f'hello, my name is {ctx.name}')

if __name__ == "__main__":
    alice.run()
```

!!! example "Run your uAgent"
    
    ``` bash
    python agent.py
    ```

You should see the message printed out every 2 seconds. You might see a message indicating insufficient funds to register, check out [remote agents](remote-agents.md) for more information about agent registration.

<div id="termynal1" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="700">
<span data-ty>Hello my name is alice.</span>
<span data-ty>Hello my name is alice.</span>
<span data-ty>Hello my name is alice.</span>
<span data-ty>Hello my name is alice.</span>
<span data-ty>Hello my name is alice.</span>
</div>

Agents can also interact with each other, for the next step go to [simple interaction](simple-interaction.md)

