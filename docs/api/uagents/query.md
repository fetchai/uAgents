<a id="src.uagents.query"></a>

# src.uagents.query

Query Envelopes.

<a id="src.uagents.query.query"></a>

#### query

```python
async def query(destination: str,
                message: Model,
                resolver: Optional[Resolver] = None,
                timeout: Optional[int] = 30) -> Optional[Envelope]
```

Query a remote agent with a message and retrieve the response envelope.

**Arguments**:

- `destination` _str_ - The destination address of the remote agent.
- `message` _Model_ - The message to send.
- `resolver` _Optional[Resolver], optional_ - The resolver to use for endpoint resolution.
  Defaults to GlobalResolver.
- `timeout` _Optional[int], optional_ - The timeout for the query in seconds. Defaults to 30.
  

**Returns**:

- `Optional[Envelope]` - The response envelope if successful, otherwise None.

<a id="src.uagents.query.enclose_response"></a>

#### enclose`_`response

```python
def enclose_response(message: Model, sender: str, session: str) -> str
```

Enclose a response message within an envelope.

**Arguments**:

- `message` _Model_ - The response message to enclose.
- `sender` _str_ - The sender's address.
- `session` _str_ - The session identifier.
  

**Returns**:

- `str` - The JSON representation of the response envelope.

<a id="src.uagents.query.enclose_response_raw"></a>

#### enclose`_`response`_`raw

```python
def enclose_response_raw(json_message: JsonStr, schema_digest: str,
                         sender: str, session: str) -> str
```

Enclose a raw response message within an envelope.

**Arguments**:

- `json_message` _JsonStr_ - The JSON-formatted response message to enclose.
- `schema_digest` _str_ - The schema digest of the message.
- `sender` _str_ - The sender's address.
- `session` _str_ - The session identifier.
  

**Returns**:

- `str` - The JSON representation of the response envelope.

