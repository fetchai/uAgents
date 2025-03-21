

# src.uagents.query

Query Envelopes.



#### query[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/query.py#L13)
```python
@deprecated(
    "Query is deprecated and will be removed in a future release, use send_sync_message instead."
)
async def query(destination: str,
                message: Model,
                resolver: Resolver | None = None,
                timeout: int = 30) -> MsgStatus | Envelope
```

Query a remote agent with a message and retrieve the response envelope.

**Arguments**:

- `destination` _str_ - The destination address of the remote agent.
- `message` _Model_ - The message to send.
- `resolver` _Resolver | None_ - The resolver to use for endpoint resolution.
  Defaults to GlobalResolver.
- `timeout` _int_ - The timeout for the query in seconds. Defaults to 30.
  

**Returns**:

  MsgStatus | Envelope: The response envelope if successful, otherwise MsgStatus.

