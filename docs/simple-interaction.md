# Agent interactions

## Add a second agent

To show μAgents interacting, we'll need to create a second agent.
Importing the `Bureau` class will allow us to create a collection of agents and run them together in the same script.
Then we can simply add agents `alice` and `bob` to the `Bureau` and run it.

```python
from uagents import Agent, Context, Bureau

alice = Agent(name="alice", seed="alice recovery phrase")
bob = Agent(name="bob", seed="bob recovery phrase")

@alice.on_interval(period=2.0)
async def say_hello(ctx: Context):
    ctx.logger.info(f'Hello, my name is {ctx.name}')

@bob.on_interval(period=2.0)
async def say_hello(ctx: Context):
    ctx.logger.info(f'Hello, my name is {ctx.name}')

bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
```

Yoy should observe alice and bob printing out their name in the terminal.

!!! example "Run your agents"
    
    ``` bash
    python simple-agents.py
    ```

You will see the message printed out every 2 seconds. You might see a message indicating insufficient funds to register, check out [agent registration](almanac-registration.md) for more information.

<div id="termynal1" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="700">
<span data-ty>Hello, my name is alice</span>
<span data-ty>Hello, my name is bob</span>
<span data-ty>Hello, my name is alice</span>
<span data-ty>Hello, my name is bob</span>
</div>

## Agent communication

To allow our agents to communicate with each other we will need a message structure, and for that, we need to import `Model` to define a generic message.

```python
from uagents import Model

class Message(Model):
    text: str

```

We can use the `send` function from the `Context` class to send a message from alice to bob on an interval.

```python
@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    msg = f'hello there {bob.name} my name is {alice.name}'
    await ctx.send(bob.address, Message(text=msg))
```

We also need to introduce a message handler for bob. We will do this inside the `on_message` decorator that will activate the `message_handler` once bob receives the message.

```python
@bob.on_message(Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.text}")
    ctx.logger.info(msg)
```

Finally, we need to add both agents to the `Bureau` in order to run them from the same script.


```python
from uagents import Agent, Context, Bureau, Model

class Message(Model):
    text: str

alice = Agent(name="alice", seed="alice recovery phrase")
bob = Agent(name="bob", seed="bob recovery phrase")

@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    msg = f'hello there {bob.name} my name is {alice.name}'
    await ctx.send(bob.address, Message(text=msg))


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.text}")


bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
```

When running the script above, you should see alice's message printed on the terminal:

!!! example "Run your agents"
    
    ``` bash
    python agent-communication.py
    ```

<div id="termynal2" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="700">
<span data-ty>[bob]: message received from agent1qww3ju3h6kfcuqf54gkghvt2pqe8qp97a7nzm2vp8plfxflc0epzcjsv79t: hello there bob my name is alice</span>
<span data-ty>[bob]: message received from agent1qww3ju3h6kfcuqf54gkghvt2pqe8qp97a7nzm2vp8plfxflc0epzcjsv79t: hello there bob my name is alice</span>
</div>

You could also try to add a response from bob to alice, for that you would need to add a `send` message from bob after alice's 
message is received and a new message handler for alice to be able to manage and print out bob's message. For a slightly more complex 
example check out the next section [remote agents](remote-agents.md).

