

# src.uagents.experimental.dialogues.__init__

Dialogue class aka. blueprint for protocols.



## Node Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L21)

```python
class Node()
```

A node represents a state in the dialogue.



## Edge Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L36)

```python
class Edge()
```

An edge represents a transition between two states in the dialogue.



#### model[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L56)
```python
@property
def model() -> Optional[Type[Model]]
```

The message model type that is associated with the edge.



#### model

```python
@model.setter
def model(model: Type[Model]) -> None
```

Set the message model type for the edge.



#### func[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L66)
```python
@property
def func() -> Optional[MessageCallback]
```

The message handler that is associated with the edge.



#### func

```python
@func.setter
def func(func: MessageCallback) -> None
```

Set the message handler that will be called when a message is received.



#### efunc[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L76)
```python
@property
def efunc() -> Optional[MessageCallback]
```

The edge handler that is associated with the edge.



#### set_edge_handler[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L81)
```python
def set_edge_handler(model: Type[Model], func: MessageCallback)
```

Set the edge handler that will be called when a message is received
This handler can not be overwritten by a decorator.



#### set_message_handler[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L91)
```python
def set_message_handler(model: Type[Model], func: MessageCallback)
```

Set the default message handler for the edge that will be overwritten if
a decorator defines a new function to be called.



## Dialogue Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L102)

```python
class Dialogue(Protocol)
```

A dialogue is a protocol with added functionality to handle the enforcement
of a sequence of messages.
The instance of this class is the local representation of the dialogue,
i.e. the definition of a pattern of messages that are exchanged between
two participants.

When defining a pattern of Nodes and Edges, the dialogue will automatically
be validated for cycles and the rules will be derived from the graph.

The only thing left to do is to add message handlers for the edges in a
known fashion, i.e. the message handler for an edge must be decorated with
the edge name and the message model type.
The message handler will be registered automatically and the message model
will be used to validate the message content.

Ex.:
    @dialogue._on_state_transition("edge_name", MessageModel)
    async def handler(ctx: Context, sender: str, message: MessageModel):
        pass

A common practice is to add additional decorators to the pattern definition
to simplify the usage of the dialogue class. This can be done by creating
creating additional decorators that call the _on_state_transition method.
Ex.:
    def on_init(model: Type[Model]):
        return super()._on_state_transition("edge_name", model)

and then use it like this:
    @pattern.on_init(MessageModel)
    async def handler(ctx: Context, sender: str, message: MessageModel):
        pass

The current features include:
- A graph representation of the dialogue, which is used to validate the
    sequence of messages.
- Session handling which includes a session storage that contains all the
    messages that were exchanged between two participants.
- Sessions will automatically be deleted after a certain amount of time.
- Access to the dialogue history through ctx.dialogue (see Context class).



#### rules[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L196)
```python
@property
def rules() -> Dict[str, List[str]]
```

Property to access the rules of the dialogue.

**Returns**:

  Dict[str, List[str]]: Dictionary of rules represented by edges.



#### get_overview[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L214)
```python
def get_overview() -> Dict
```

Get an overview of the dialogue structure.

**Returns**:

- `Dict` - Manifest like representation of the dialogue structure.



#### is_starter[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L314)
```python
def is_starter(digest: str) -> bool
```

Return True if the digest is the starting message of the dialogue.
False otherwise.



#### is_ender[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L321)
```python
def is_ender(digest: str) -> bool
```

Return True if the digest is one of the last messages of the dialogue.
False otherwise.



#### get_current_state[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L328)
```python
def get_current_state(session_id: UUID) -> str
```

Get the current state of the dialogue for a given session.



#### is_finished[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L332)
```python
def is_finished(session_id: UUID) -> bool
```

Return True if the current state is (one of) the ending state(s).
False otherwise.



#### update_state[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L428)
```python
def update_state(digest: str, session_id: UUID) -> None
```

Update the state of a dialogue session and create a new session
if it does not exist.

**Arguments**:

- `digest` _str_ - The digest of the message to update the state with.
- `session_id` _UUID_ - The ID of the session to update the state for.



#### cleanup_conversation[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L445)
```python
def cleanup_conversation(session_id: UUID) -> None
```

Removes all messages related with the given session from the dialogue instance.



#### add_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L450)
```python
def add_message(session_id: UUID, message_type: str, schema_digest: str,
                sender: str, receiver: str, content: JsonStr,
                **kwargs) -> None
```

Add a message to the conversation of the given session within the dialogue instance.



#### get_conversation[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L479)
```python
def get_conversation(session_id: UUID,
                     message_filter: Optional[str] = None) -> List[Any]
```

Return the message history of the given session from the dialogue instance as
list of DialogueMessage.
This includes both sent and received messages.

**Arguments**:

- `session_id` _UUID_ - The ID of the session to get the conversation for.
- `message_filter` _str_ - The name of the message type to filter for
  

**Returns**:

- `list(DialogueMessage)` - A list of all messages exchanged during the given session
- `list(DialogueMessage)` - Only messages of type 'message_filter' (Model.__name__)
  from the given session



#### get_edge[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L506)
```python
def get_edge(edge_name: str) -> Edge
```

Return an edge from the dialogue instance.



#### is_valid_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L514)
```python
def is_valid_message(session_id: UUID, msg_digest: str) -> bool
```

Check if an incoming message is valid for a given session.

**Arguments**:

- `session_id` _UUID_ - The ID of the session to check the message for.
- `msg_digest` _str_ - The digest of the message to check.
  

**Returns**:

- `bool` - True if the message is valid,
  False otherwise.



#### is_valid_reply[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L535)
```python
def is_valid_reply(in_msg: str, out_msg: str) -> bool
```

Check if a reply is valid for a given message.

**Arguments**:

- `in_msg` _str_ - The digest of the message to check the reply for.
- `out_msg` _str_ - The digest of the reply to check.
  

**Returns**:

- `bool` - True if the reply is valid, False otherwise.



#### is_included[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L550)
```python
def is_included(msg_digest: str) -> bool
```

Check if a message is included in the dialogue.

**Arguments**:

- `msg_digest` _str_ - The digest of the message to check.
  

**Returns**:

- `bool` - True if the message is included, False otherwise.



#### manifest[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L616)
```python
def manifest() -> Dict[str, Any]
```

This method will add the dialogue structure to the original manifest
and recalculate the digest.



#### start_dialogue[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L641)
```python
async def start_dialogue(ctx: Context, destination: str,
                         message: Model) -> List[MsgStatus]
```

Start a dialogue with a message.

**Arguments**:

- `ctx` _Context_ - The current message context
- `destination` _str_ - Either the agent address of the receiver or a protocol digest
- `message` _Model_ - The current message to send
  

**Raises**:

- `ValueError` - If the dialogue is not started with the specified starting message.



#### initialise_cleanup_task[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dialogues/__init__.py#L688)
```python
def initialise_cleanup_task(interval: int = 1) -> None
```

Initialise the cleanup task.

Deletes sessions that have not been used for a certain amount of time.
The task runs every second so the configured timeout is currently
measured in seconds as well (interval time * timeout parameter).
Sessions with 0 as timeout will never be deleted.

*Important*:
- setting the interval above 1 will act as a multiplier
- setting it to 0 will disable the cleanup task

