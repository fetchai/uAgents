# Remote agents

μAgents can also interact remotely from different locations across the internet. All you need to know is the recipient agent's address to query it's information in the [Almanac contract](almanac-overview.md).
See [Addresses](addresses.md) for more information about μAgent addresses.

In this example, we will simulate remote communication between agents by running two agents on different ports and terminals on the same device.

## Alice

We will start by defining agent `alice` and the recipient address (`bob`'s address in this example). Then we will include 
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
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    alice.run()
```


## Bob

In a different script, we will define agent `bob` with just a message handler to print out `alice`'s messages and respond to her afterward.

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


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="hello there alice"))


if __name__ == "__main__":
    bob.run()
```

Now, we first run `bob` and then `alice` from different terminals. They will register automatically in the Almanac contract using their funds. The received messages will print out in each terminal.

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

For a more complex example visit [restaurant booking demo](booking-demo.md).

## The Agentverse Mailbox

Local μAgents can also interact remotely using a mailbox server. For example, you can use [The Agentverse Explorer](https://agentverse.ai/) to find other agents and register your own.

To register agents in the Agentverse mailbox, you need to sign in at [The Agentverse Explorer](https://agentverse.ai/). Then, in the upper right corner click on your profile and select `API Keys`, select `Create new key` and name it. This will generate your own `API Key` that will allow you to use the mailbox server.

Then, navigate to the `Mailroom` tab and select `+ Mailbox` to register an agent, you need to select a name for it and provide the agent's address. Finally, you need to define the μAgent specifying the mailbox server and the `API Key`

```python
# First generate a secure seed phrase (e.g. https://pypi.org/project/mnemonic/)
SEED_PHRASE = "put_your_seed_phrase_here"

# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

# Then sign up at https://agentverse.ai to get an API key and register your agent
API_KEY = "put_your_API_key_here"

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="alice",
    seed=SEED_PHRASE,
    mailbox=f"{API_KEY}@https://agentverse.ai",
)
```

Now, you can recreate the example we showed at the begining of this section also registering agent `bob` in [The Agentverse Explorer](https://agentverse.ai/) and adding the missing imports, models and handlers.


## Managed Agents on Agentverse

Agentverse is both a sandbox for experimentation and learning and a place to deploy your agents so you don't have to keep them running yourself. You can also choose from a set of use case examples.

To get started go to [The Agentverse Explorer](https://agentverse.ai/) and sign in. Then, click on `Managed Agents` and select `+ Use Case`. You can start by selecting `Your first agent` use case in the `Getting Started` section to create a simple agent that prints a hello statement. Now, select your new `My First Agent` agent to open the playground. Click on the `Run` button and you will see the following printed on the terminal:

<div id="termynal3" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="2000">
<span data-ty>Hello, I'm an agent and my address is agent1...</span>
<span data-ty>Hello, I'm an agent and my address is agent1...</span>
<span data-ty>Hello, I'm an agent and my address is agent1...</span>
<span data-ty>...</span>
</div>

You can try the `Sending messages between agents` use case to establish communication between two agents on the `agentverse`. Feel free to try other use cases or create customized agents of your own! 


## Agentverse and Local Agents
Communication between agentverse agents and local agents is also possible. All you need to do is provide the target address of the agent.
After registering agent `alice` on the mailbox server, as explained in the previous section, you can easily create a new agentverse agent `bob` by selecting `+ Agent` on `Managed Agents` in the [The Agentverse Explorer](https://agentverse.ai/). Then, add the following code to `bob`:


```python
class Message(Model):
    message: str

@agent.on_message(model=Message)
async def handle_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    await ctx.send(sender, Message(message="hello there alice"))
```

Next, copy bob's address and paste it into alice's code under `RECIPIENT_ADDRESS`. Once you've done that, run agent `bob` on [The Agentverse Explorer](https://agentverse.ai/) followed by your local agent `alice`. You'll then be able to send messages back and forth between the two agents, which will be displayed on both alice's and bob's terminals.
