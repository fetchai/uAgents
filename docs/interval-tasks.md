# Interval tasks

μAgents can use interval tasks to periodically perform actions with some time interval.

We can use the `on_interval` decorator to repeat a task in a specified period.
We also need to import `Context` to have access to the information that the agent needs to function.
In this case, we will just define a `say_hello` function that will print out the agent name every 2 seconds.

```python
from uagents import Agent, Context

alice = Agent(name="alice")

@alice.on_interval(period=2.0)
async def say_hello(ctx: Context):
    ctx.logger.info(f'hello, my name is {ctx.name}')

if __name__ == "__main__":
    alice.run()
```

!!! example "Run your agent"
    
    ``` bash
    python agent.py
    ```

You should see the message printed out in the terminal every 2 seconds. 

<div id="termynal1" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="200">
<span data-ty>Hello my name is alice.</span>
<span data-ty>Hello my name is alice.</span>
<span data-ty>Hello my name is alice.</span>
<span data-ty>Hello my name is alice.</span>
</div>

For another interval task example see [agent communication](simple-interaction.md).