# Running an agent

## Create the agent

You can create your first uAgent with the following python script

```python
from uagents import Agent, Context

alice = Agent(name="alice", seed="alice recovery phrase")
```

It is optional but useful to include a `seed` parameter when creating an agent to set fixed [addresses](addresses.md). Otherwise, random addresses will be generated every time you run the agent.


## Give the agent something to do

Let's start with a simple task of saying hello every 2 seconds:
```python
@alice.on_interval(period=2.0)
async def say_hello(ctx: Context):
    print(f'hello, my name is {ctx.name}')
```
The `Context` object is a collection of data and functions related to the agent. In this case, we just use the agent's name.

## Run the agent

You can now run your first uAgent!

```python
from uagents import Agent, Context

alice = Agent(name="alice", seed="alice recovery phrase")

@alice.on_interval(period=2.0)
async def say_hello(ctx: Context):
    print(f'hello, my name is {ctx.name}')

if __name__ == "__main__":
    alice.run()

```
!!! example "Run your agent"
    
    ``` bash
    python agent.py
    ```

After a few lines in the agent's logs, you should see the following printed on your terminal:

<div id="termynal1" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="2000">
<span data-ty>hello, my name is alice.</span>
<span data-ty>hello, my name is alice.</span>
<span data-ty>hello, my name is alice.</span>
<span data-ty>...</span>
</div>
