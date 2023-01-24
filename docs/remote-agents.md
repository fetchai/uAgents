# Remote agents

uAgents can also interact remotely from different terminals. All you need to know is the recipient agent's address to query it's information in the [almanact contract](almanac-overview.md).
You can print your uAgent's address at any time by printing `agent_name.address` in your python script.

## Alice

We will start by defining agent alice and the recipient address (bob's address). Then we will include 
a send function and a handler as we have learned in [agent interactions](simple-interaction.md):

```python
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model


class Message(Model):
    message: str


RECIPIENT_ADDRESS = "agent1q2kxet3vh0scsf0sm7y2erzz33cve6tv5uk63x64upw5g68kr0chkv7hw50"

alice = Agent(
    name="alice",
    port=8000,
    seed="alice secret phrase",
    endpoint=["http://127.0.0.1:8000/submit"],
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
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model


class Message(Model):
    message: str


bob = Agent(
    name="bob",
    port=8001,
    seed="bob secret phrase",
    endpoint=["http://127.0.0.1:8001/submit"],
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

!!! example "Run Bob and Alice"
    
    ``` bash
    python bob.py
    python alice.py
    ```

In bob's terminal:

<div id="termynal1" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="700">
<span data-ty>INFO:root:Adding funds to agent...complete</span>
<span data-ty>INFO:root:Registering Agent bob...</span>
<span data-ty>INFO:root:Registering Agent bob...complete.</span>
<span data-ty>Wallet address: fetch1cr9ghmxrf943dmw484ma3v3nz2v0q6u9pynqdk</span>
<span data-ty>[bob] From: agent1qdp9j2ev86k3h5acaayjm8tpx36zv4mjxn05pa2kwesspstzj697xy5vk2a hello there bob</span>
<span data-ty>[bob] From: agent1qdp9j2ev86k3h5acaayjm8tpx36zv4mjxn05pa2kwesspstzj697xy5vk2a hello there bob</span>
<span data-ty>[bob] From: agent1qdp9j2ev86k3h5acaayjm8tpx36zv4mjxn05pa2kwesspstzj697xy5vk2a hello there bob</span>
</div>


In alice's terminal:

<div id="termynal2" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="700">
<span data-ty>INFO:root:Adding funds to agent...complete</span>
<span data-ty>INFO:root:Registering Agent alice...</span>
<span data-ty>INFO:root:Registering Agent alice...complete.</span>
<span data-ty>Wallet address: fetchnfu3hd87323mw484ma3v3nz2v0q6uhds7d</span>
<span data-ty>[alice] From: agent5kdyfj2ev86k3h5acaa93kdnch8shv4mjxn05pa2kwesspstzj023jdus93j hello there alice</span>
<span data-ty>[alice] From: agent5kdyfj2ev86k3h5acaa93kdnch8shv4mjxn05pa2kwesspstzj023jdus93j hello there alice</span>
<span data-ty>[alice] From: agent5kdyfj2ev86k3h5acaa93kdnch8shv4mjxn05pa2kwesspstzj023jdus93j hello there alice</span>
</div>

For a more complex example visit [restaurant booking demo](booking-demo.md)