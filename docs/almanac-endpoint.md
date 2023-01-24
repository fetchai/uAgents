# Endpoint weighting

When an agent registers in the almanac contract, it must specify the service endpoints that they provide along with a weight parameter for each endpoint. Then, when any agent tries to communicate with your agent, the service endpoint will be chosen using a weighted random selection.

You will have two format options when defining your agent's endpoints:

## List format

Define your agent's endpoints as a list of strings, the weights will be automatically assigned a value of 1.

```python
agent = Agent(
    name="alice",
    port=8000,
    seed="agent secret phrase",
    endpoint=["http://127.0.0.1:8000/submit","http://127.0.0.1:8001/submit"]
)
```

## Dict format

Define your agent's endpoints in a Dict format specifying the weight for each endpoint, if the weight parameter is not specified, it will be assigned a value of 1.

```python
agent = Agent(
    name="alice",
    port=8000,
    seed="agent recovery seed phrase",
    endpoint={
        "http://127.0.0.1:8000/submit": {"weight": 2},
        "http://127.0.0.1:8001/submit": {}, # weight value = 1
    },
)
```
