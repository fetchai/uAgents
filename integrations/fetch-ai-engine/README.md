# UAgents AI-Engine Integration

## 📌 Overview

This package provides the necessary types for integrating AI-Engine with UAgents, enabling structured responses and request handling within the UAgents framework. It includes models for handling various response types, key-value pairs, and booking requests.

## Installation

To install the package, use the following command:

```bash
pip install uagents-ai-engine
```

## Usage

### Importing the Package

To use the models provided by this package, import them as follows:

```python
from ai_engine.chitchat import ChitChatDialogue
from ai_engine.messages import DialogueMessage
from ai_engine.dialogue import EdgeMetadata, EdgeDescription
```

The `chitchat`, `messages`, and `dialogue` modules provide essential classes, types, and functions to facilitate structured and dynamic interactions with the agent. These modules support an open-ended communication model, allowing users to engage in an ongoing dialogue with the agent. After each user message, the agent responds, enabling a continuous and interactive conversation that can proceed as long as needed.

```python
from ai_engine.types import UAgentResponseType, KeyValue, UAgentResponse, BookingRequest
```

The `types` module offers a comprehensive set of models for handling responses, key-value pairs, and booking requests. This module is designed for scenarios where a single exchange is sufficient. The user sends a message, receives a well-structured response from the agent, and the interaction concludes efficiently. This approach is ideal for straightforward queries and tasks.

### 📦 Components

### 1. Response Models

The following classes are used for non-dialogue agent communication.

#### UAgentResponseType

An enumeration defining the types of responses that an agent can provide:

```python
class UAgentResponseType(Enum):
    FINAL = "final"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"
    SELECT_FROM_OPTIONS = "select_from_options"
    FINAL_OPTIONS = "final_options"
```

#### KeyValue

A model representing a key-value pair. It is usually used by the AI-Engine as a way to provide multiple choice options to the user:

```python
class KeyValue(Model):
    key: str
    value: str
```

#### UAgentResponse

A model for structuring the response from an agent:

```python
class UAgentResponse(Model):
    version: Literal["v1"] = "v1"
    type: UAgentResponseType
    request_id: Optional[str]
    agent_address: Optional[str]
    message: Optional[str]
    options: Optional[List[KeyValue]]
    verbose_message: Optional[str]
    verbose_options: Optional[List[KeyValue]]
```

**Attributes:**

- `version`: The version of the response model (default is "v1").
- `type`: The type of the response, based on `UAgentResponseType`.
- `request_id`: An optional identifier for the request.
- `agent_address`: An optional address of the agent.
- `message`: An optional message from the agent.
- `options`: An optional list of key-value options.
- `verbose_message`: An optional verbose message from the agent.
- `verbose_options`: An optional list of verbose key-value options.

#### BookingRequest

A model for handling booking requests:

```python
class BookingRequest(Model):
    request_id: str
    user_response: str
    user_email: str
    user_full_name: str
```

**Attributes:**

- `request_id`: The unique identifier for the booking request.
- `user_response`: The response from the user.
- `user_email`: The email address of the user.
- `user_full_name`: The full name of the user.

### 2. Dialogue Management

#### ChitChatDialogue

A specific dialogue class for AI-Engine enabled chit-chat:

```python
class ChitChatDialogue(Dialogue):
    def on_initiate_session(self, model: Type[Model]):
        # ... (session initiation logic)

    def on_reject_session(self, model: Type[Model]):
        # ... (session rejection logic)

    def on_start_dialogue(self, model: Type[Model]):
        # ... (dialogue start logic)

    def on_continue_dialogue(self, model: Type[Model]):
        # ... (dialogue continuation logic)

    def on_end_session(self, model: Type[Model]):
        # ... (session end logic)
```

How to initialize a `ChitChatDialogue` instance:

```python

agent = Agent()

# instantiate the dialogues
chitchat_dialogue = ChitChatDialogue(
    version="0.1",
    storage=agent.storage,
)
```

For a more in depth example, see the [ChitChatDialogue](https://github.com/fetchai/uAgents/blob/main/integrations/fetch-ai-engine/examples/simple_agent.py) example.

### 3. Extending Dialogue with Metadata

#### EdgeMetadata

Metadata for the edges to specify targets and observability:

- `system` implies AI Engine processing
- `user` is direct message to the user
- `ai` is a message to the AI Engine
- `agent` is a message to the agent.

```python
class EdgeMetadata(BaseModel):
    target: Literal["user", "ai", "system", "agent"]
    observable: bool
```

#### EdgeDescription

A structured description for the edge:

```python
class EdgeDescription(BaseModel):
    description: str
    metadata: EdgeMetadata
```

### Create Edge Function

Function to create an edge with metadata:

```python
init_session = create_edge(
    name="Initiate session",
    description="Every dialogue starts with this transition.",
    target="user",
    observable=True,
    parent=default_state,
    child=init_state,
)
```

### 3. Message Types

The following classes are used for dialogue agent communication.

#### BaseMessage

A base model for all messages:

```python
class BaseMessage(Model):
    message_id: UUID
    timestamp: datetime
```

#### DialogueMessage

A model for generic dialogue messages:

```python
class DialogueMessage(BaseMessage):
    type: Literal["agent_message", "agent_json", "user_message"]
    agent_message: Optional[str]
    agent_json: Optional[AgentJSON]
    user_message: Optional[str]
```

Can be initialized as follows, we'll call this class `ChitChatDialogueMessage`:

```python
class ChitChatDialogueMessage(DialogueMessage):
    """ChitChat dialogue message"""

    pass
```

And then use it as follows:

```python
@chitchat_dialogue.on_continue_dialogue(ChitChatDialogueMessage)
```

Where `chitchat_dialogue` is defined above in the `ChitChatDialogue` section and `on_continue_dialogue` is a method of the `ChitChatDialogue` class that can be extended.

## AI-Engine Integration

This integration adds the required types for AI-Engine to interact with UAgents effectively. The `UAgentResponse` model serves as the primary structure for agent responses, while `BookingRequest` handles user booking requests.

### Digest

`UAgentResponse` digest:

```
model:cf0d1367c5f9ed8a269de559b2fbca4b653693bb8315d47eda146946a168200e
```
