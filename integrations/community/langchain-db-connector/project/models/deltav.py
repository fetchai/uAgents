from enum import Enum
from typing import List, Literal, Optional

from pydantic import Field
from uagents import Model


class DatabasePrompt(Model):
    prompt: str = Field(
        description=(
            "The prompt to send to the database agent for a response. "
            "This prompt will be used to query one of the databases of the "
            "agent to get information."
        )
    )


class UAgentResponseType(Enum):
    FINAL = "final"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"
    SELECT_FROM_OPTIONS = "select_from_options"
    FINAL_OPTIONS = "final_options"


class KeyValue(Model):
    key: str
    value: str


class UAgentResponse(Model):
    version: Literal["v1"] = "v1"
    type: UAgentResponseType
    request_id: Optional[str]
    agent_address: Optional[str]
    message: Optional[str]
    options: Optional[List[KeyValue]]
    verbose_message: Optional[str]
    verbose_options: Optional[List[KeyValue]]
