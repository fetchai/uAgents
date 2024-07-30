# UAgents AI-Engine Integration

## 📌 Overview

This package provides the necessary types for integrating AI-Engine with UAgents, enabling structured responses and request handling within the UAgents framework. It includes models for handling various response types, key-value pairs, and booking requests.

## Installation

To install the package, use the following command:

```bash
pip install uagents
```

## Usage

### Importing the Package

To use the models provided by this package, import them as follows:

```python
from ai_engine.types import UAgentResponseType, KeyValue, UAgentResponse, BookingRequest
```

### Models

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

## AI-Engine Integration

This integration adds the required types for AI-Engine to interact with UAgents effectively. The `UAgentResponse` model serves as the primary structure for agent responses, while `BookingRequest` handles user booking requests.

### Digest

`UAgentResponse` digest:

```
model:66841ea279697fd62a029c37b7297e4097966361407a2cc49cd1e7defb924685
```
