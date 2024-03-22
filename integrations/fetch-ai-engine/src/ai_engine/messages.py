from pydantic import BaseModel, Field, Field
from uuid import UUID, uuid4
from datetime import datetime, UTC
from typing import Optional, List, Annotated, Optional, Literal, Union


# here are some message types that is currently supported by DeltaV


class BaseMessage(BaseModel):
  """Base message model for all messages"""

  # message id, for each new message it should be a unique id
  message_id: UUID = Field(default_factory=uuid4)

  # timestamp of the message creation
  timestamp: datetime = Field(default_factory=datetime.now(UTC))


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


class AgentTextMessage(BaseMessage):
  """Agent text message"""

  # type
  type: Literal["agent_message"] = "agent_message"

  # agent message, this is the text that the agent wants to send to the user
  agent_message: str


class AgentJSONMessage(BaseMessage):
  """Agent JSON message, to map to UI elements"""

  # type
  type: Literal["agent_json"] = "agent_json"

  # agent JSON message
  agent_json: AgentJSON


# Annotated message type to allow for different types of messages
AgentMessage = Annotated[
    Union[
        AgentTextMessage,
        AgentJSONMessage,
    ],
    Field(discriminator="type"),
]
