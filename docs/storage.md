
# Storage

You can store information using the agent's local storage by simply running:
```python
ctx.storage.set("key", "value")
```
within a handler, where `ctx` is the agent's `Context` object.

This will save the information in a JSON file, you can retreive it a any time using:

```python
 ctx.storage.get("key")
```


See the [restaurant booking demo](booking-demo.md) for an example that makes use of the agent's storage to store table information.