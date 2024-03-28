from pydantic import BaseModel, Field, Extra
from typing import Optional
from uagents import Model
from uuid import UUID, uuid4
from datetime import datetime, UTC
from typing import Optional, List, Annotated, Optional, Literal, Union


# here are some message types that is currently supported by DeltaV


class KeyValue(BaseModel):
    """Key value pair for options"""

    # key of the option
    key: Union[int, str]

    # value of the option
    value: str


class AgentJSON(BaseModel):
    """Agent JSON message"""

    # type identifier
    # on DeltaV we can map these types to UI elements
    # available on DeltaV: options (maps to select buttons), date (date picker)
    type: str

    # text to be presented before the UI element
    text: Optional[str] = None

    # options for the user to select from
    options: Optional[List[KeyValue]] = None


### IMPORTANT NOTE ###
# If the expected model doesn't have any field -> AI Engine automatically send the expected empty message (if there are more edges user will select which edge to go next)
# If there are fields in the expected model, there is two case:
#   1. Generic Model: AI Engine is going to trigger context building and build the required JSON
#   2. Model inherits BaseMessage: if message_id: UUID, timestamp: datetime fields are present, AI Engine is going to wait for the user to send UserMessage via API / DeltaV UI
class BaseMessage(Model):
    """Base message model for all messages"""

    # message id, for each new message it should be a unique id
    message_id: UUID = Field(
        default_factory=uuid4,
        description="Unique message ID, never ask for this. Ignore this field! It's set automatically.",
    )

    # timestamp of the message creation
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp of the message creation. Ignore this field! It's set automatically.",
    )

    class Config:
        extra = Extra.allow


class DialogueMessage(BaseMessage):
    """Generic dialogue message"""

    # type
    type: Literal["agent_message", "agent_json", "user_message"] = Field(
        default="user_message",
        description="Type of message, don't ask for this. Ignore this field! It's set automatically.",
    )

    # agent messages, this is the text that the agent wants to send to the user
    agent_message: Optional[str] = Field(
        default=None, description="The message that the agent wants to send to the user"
    )
    agent_json: Optional[AgentJSON] = Field(
        default=None,
        description="Agent JSON message, to map to UI elements. Ignore this field! It's set automatically.",
    )

    # user messages, this is the text that the user wants to send to the agent
    user_message: Optional[str] = Field(
        default=None,
        description="The message that the user sent to the agent. Always Ask the user what message they want to send to the agent!",
    )
