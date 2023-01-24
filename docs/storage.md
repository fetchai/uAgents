
# Storage

You can store information using the agent's storage by simply running:

```python
agent._storage.set("key", "value")
```

This will save the information in a JSON file, you can retreive it a any time using:

```python
 agent._storage.get("key")
```


The [restaurant booking demo](booking-demo.md) example makes use of the agent's storage to store tables information.