<a id="src.uagents.query"></a>

# src.uagents.query

Query Envelopes.

<a id="src.uagents.query.query"></a>

#### query

```python
async def query(destination: str,
                message: Model,
                resolver: Optional[Resolver] = None,
                timeout: int = 30) -> Union[MsgStatus, Envelope]
```

Query a remote agent with a message and retrieve the response envelope.

**Arguments**:

- `destination` _str_ - The destination address of the remote agent.
- `message` _Model_ - The message to send.
- `resolver` _Optional[Resolver], optional_ - The resolver to use for endpoint resolution.
  Defaults to GlobalResolver.
- `timeout` _int_ - The timeout for the query in seconds. Defaults to 30.
  

**Returns**:

- `Optional[Envelope]` - The response envelope if successful, otherwise None.

