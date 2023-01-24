# Running an agent

You can create your first uAgent with the following python script

```python
from uagents import Agent
alice = Agent(name="alice")
```

It is useful to include a `seed` parameter when creating an agent to set fixed [addresses](addresses.md). Otherwise, random [addresses](addresses.md) will be generated every time you run agent alice.

```python
alice = Agent(name="alice", seed="alice recovery phrase")
```

## Run agent

You can now run your first uAgent!

```python
from uagents import Agent

alice = Agent(name="alice", seed="alice recovery phrase")

print(f'Hello my name is {alice.name}')

```
!!! example "Run your agent"
    
    ``` bash
    python agent.py
    ```

You should see the following printed on your terminal:

<div id="termynal1" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="700">
<span data-ty>Hello my name is alice.</span>
</div>
