# uAgents Interaction

## Communication

Below we show an example of how to create two agents that send simple messages to each other.

### uAgent alice

Aside from the name, you can also specify a seed phrase to retrieve specific addresses for your uAgent each time you run it. You need to specify a port and an HTTP endpoint so that when another uAgent queries the smart contract almanac using your uAgent's address it can communicate effectively.

As mentioned before, uAgent alice will only need the address of the recipient uAgent. We define it in the script below

```python
from nexus.setup import fund_agent_if_low
from nexus import Agent, Context, Model


class Message(Model):
    message: str


RECIPIENT_ADDRESS = "agent1qv73me5ql7kl30t0grehalj0aau0l4hpthp4m5q9v4qk2hz8h63vzpgyadp"

agent = Agent(
    name="alice",
    port=8000,
    seed="agent1 secret phrase",
    endpoint="http://127.0.0.1:8000/submit",
)

# This on_interval agent function performs an action on a defined period.
# The Context.send function sends a message to the specified uAgent address


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(RECIPIENT_ADDRESS, Message(message="hello there bob"))


# This on_message agent function activates when a message is received
# Here the senders message will be printed

@agent.on_message(model=Message)
async def on_message(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")


if __name__ == "__main__":
    agent.run()
```

### uAgent bob

We now create another script to run uAgent bob, it will be very similar to uAgent alice script but now it will only use the agent `on_message` function to react to alice's message.

```python
from nexus.setup import fund_agent_if_low
from nexus import Agent, Context, Model


class Message(Model):
    message: str


agent = Agent(
    name="bob",
    port=8001,
    seed="agent2 secret phrase",
    endpoint="http://127.0.0.1:8001/submit",
)

@agent.on_message(model=Message)
async def bob_rx_message(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="hello there alice"))


if __name__ == "__main__":
    agent.run()
```

To run the uAgents, you first need to run uAgent bob's script to have him waiting and available to respond to an incoming message. Then you can run alice's script to start the interaction. You will observe something like this:


```
INFO:root:Agent alice registration is up to date                    
Wallet address: fetch1twvhcnk7tdr08vsree7z0phj244vhfzvqwm3a6
INFO:     Started server process [20188]
INFO:     Waiting for application startup.
INFO:     ASGI 'lifespan' protocol appears unsupported.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:63968 - "POST /submit HTTP/1.1" 200 OK
[alice] From: agent1qv73me5ql7kl30t0grehalj0aau0l4hpthp4m5q9v4qk2hz8h63vzpgyadp hello there alice
INFO:     127.0.0.1:63970 - "POST /submit HTTP/1.1" 200 OK
[alice] From: agent1qv73me5ql7kl30t0grehalj0aau0l4hpthp4m5q9v4qk2hz8h63vzpgyadp hello there alice
INFO:     127.0.0.1:63972 - "POST /submit HTTP/1.1" 200 OK
[alice] From: agent1qv73me5ql7kl30t0grehalj0aau0l4hpthp4m5q9v4qk2hz8h63vzpgyadp hello there alice
```

```
INFO:root:Agent bob registration is up to date                    
Wallet address: fetch1f3yqerdl0q5dj78727q8nw5avwqxmxvd3am4vw
INFO:     Started server process [20170]
INFO:     Waiting for application startup.
INFO:     ASGI 'lifespan' protocol appears unsupported.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     127.0.0.1:63967 - "POST /submit HTTP/1.1" 200 OK
[bob  ] From: agent1qv2l7qzcd2g2rcv2p93tqflrcaq5dk7c2xc7fcnfq3s37zgkhxjmq5mfyvz hello there bob
INFO:     127.0.0.1:63969 - "POST /submit HTTP/1.1" 200 OK
[bob  ] From: agent1qv2l7qzcd2g2rcv2p93tqflrcaq5dk7c2xc7fcnfq3s37zgkhxjmq5mfyvz hello there bob
INFO:     127.0.0.1:63971 - "POST /submit HTTP/1.1" 200 OK
```

In this case, both agents appear with registration up to date, if they arent a message will show that the registration is in process and notify once is completed. If the uAgents fetch address doesnt have any funds, an exception will show notifying that funds need to be added.
