from uagents import Model
from enum import Enum
from typing import Optional, List, Literal


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


class BookingRequest(Model):
    request_id: str
    user_response: str
    user_email: str
    user_full_name: str
