# Remote agents

uAgents can also interact remotely from different terminals. All you need to know is the recipient agent's address.
You can print your uAgent's address at any time by printing `my_agent.address` in your python script.

## Registration

Agent registration in the almanac-contract is a key part for remote agents communication. Each uAgent needs to register (paying a small fee) in order to be found by other uAgents. Therefore, your agents need to have funds available in their `fetch network address`. You can use the function `fund_agent_if_low` to fund your agent:

```python
from nexus.setup import fund_agent_if_low
agent = Agent(name="alice", seed="agent1 secret phrase")

fund_agent_if_low(agent.wallet.address())
```
This function will check if you have enough tokens to register in the `almanac-contract`, if not it will add tokens to your `fetch network address`. Make sure to add a `seed` to your agent so you don't have to fund different addresses each time you run your agent.

uAgents can communicate by querying the `almanac-contract` and retrieving an HTTP endpoint from the recipient uAgent. Therefore, we need to specify a service endpoint and a port when defining an agent:

```python
agent = Agent(
    name="alice",
    port=8000,
    seed="agent1 secret phrase",
    endpoint="http://127.0.0.1:8000/submit",
)
```

Here we defined a local http address, but you could also define a remote address to allow agent communication over different machines through the internet.

## Alice

We will start by defining agent alice and the recipient address (bob's address). Then we will include 
a send function and a handler as we have learned in the previous section:

```python
from nexus.setup import fund_agent_if_low
from nexus import Agent, Context, Model


class Message(Model):
    message: str


RECIPIENT_ADDRESS = "agent1q2kxet3vh0scsf0sm7y2erzz33cve6tv5uk63x64upw5g68kr0chkv7hw50"

alice = Agent(
    name="alice",
    port=8000,
    seed="alice secret phrase",
    endpoint="http://127.0.0.1:8000/submit",
)

fund_agent_if_low(alice.wallet.address())


@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(RECIPIENT_ADDRESS, Message(message="hello there bob"))


@alice.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")


if __name__ == "__main__":
    alice.run()
```


## Bob

In a different script, we will define agent bob with just a message handler to print out alice message and respond to her afterward.

```python
from nexus.setup import fund_agent_if_low
from nexus import Agent, Context, Model


class Message(Model):
    message: str


bob = Agent(
    name="bob",
    port=8001,
    seed="bob secret phrase",
    endpoint="http://127.0.0.1:8001/submit",
)

fund_agent_if_low(bob.wallet.address())

print("bob address: ", bob.address)

@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="hello there alice"))


if __name__ == "__main__":
    bob.run()
```

Now, we first run bob and then alice from different terminals, they will register automatically in the `almanac-contract` using their funds. The received messages will print out in each terminal.


In bob's terminal:
```
[bob] From: agent1qdp9j2ev86k3h5acaayjm8tpx36zv4mjxn05pa2kwesspstzj697xy5vk2a hello there bob
```

In alice's terminal:

```
[alice] From: agent1q2kxet3vh0scsf0sm7y2erzz33cve6tv5uk63x64upw5g68kr0chkv7hw50 hello there alice
```

For a more complex example visit [restaurant booking demo](booking-demo.md)