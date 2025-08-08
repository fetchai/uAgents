from enum import Enum
from typing import Literal

from uagents import Model


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
    request_id: str | None = None
    agent_address: str | None = None
    message: str | None = None
    options: list[KeyValue] | None = None
    verbose_message: str | None = None
    verbose_options: list[KeyValue] | None = None


class BookingRequest(Model):
    request_id: str
    user_response: str
    user_email: str
    user_full_name: str
