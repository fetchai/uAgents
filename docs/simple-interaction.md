# Simple agents interactions

## Add a second agent

First we need to import `Bureau` that will allow us to have a collection of agents and run them together.
Then we can simply add agents `alice` and `bob` to the Bureau and run it.

```python
from nexus import Agent, Context, Bureau

alice = Agent(name="alice", seed="alice recovery phrase")
bob = Agent(name="bob", seed="bob recovery phrase")

@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    print(f'My name is {ctx.name}')

@bob.on_interval(period=2.0)
async def send_message(ctx: Context):
    print(f'My name is {ctx.name}')

bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
```

Yoy should observe alice and bob printing out their name in the terminal.

```
My name is alice
My name is bob
My name is alice
My name is bob
...
```

## Agent communication

To allow our agents communicate with eachother we will need a message structure, for that we need to impor `Model` to define a generic message.

```python
from nexus import Model

class Message(Model):
    text: str

```

We can use the `send` function from the `Context` class to send a message from alice to bob on an interval.

```python
@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    msg = f'hello there {bob.name} my name is {alice.name}'
    await ctx.send(bob.address,Message(text=msg))
```

We also need to intoduce a message handler for bob. We will do this inside the `on_message` decorator that will activate the `message_handler`  once bob receives the message.

```python
@bob.on_message(Message)
async def message_handler(sender: str, msg: Message):
    print(f"message received from {sender}:")
    print(msg)
```

Finally, we need to add both agents to the `Bureau` in order to run the simultaneously


```python
from nexus import Agent, Context, Bureau, Model

class Message(Model):
    text: str

alice = Agent(name="alice", seed="alice recovery phrase")
bob = Agent(name="bob", seed="bob recovery phrase")

@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    msg = f'hello there {bob.name} my name is {alice.name}'
    await ctx.send(bob.address,Message(text=msg))

@bob.on_message(Message)
async def message_handler(sender: str, msg: Message):
    print(f"message received from {sender}:")
    print(msg)

bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
```

