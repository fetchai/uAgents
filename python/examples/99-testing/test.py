from enum import Enum
from typing import List, Literal, Optional

from pydantic import Field

from uagents import Model


class SimpleModel(Model):
    name: str
    age: int
    flag: bool = False


class UAgentResponseType(Enum):
    FINAL = "final"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"
    SELECT_FROM_OPTIONS = "select_from_options"
    FINAL_OPTIONS = "final_options"


class KeyValue(Model):
    key: str
    value: str = Field(..., description="The value of the key.")


class UAgentResponse(Model):
    version: Literal["v1"] = "v1"
    type: UAgentResponseType
    request_id: Optional[str] = None
    agent_address: Optional[str] = None
    message: Optional[str] = None
    options: Optional[List[KeyValue]] = None
    verbose_message: Optional[str] = None
    verbose_options: Optional[List[KeyValue]] = None


if __name__ == "__main__":
    x = UAgentResponse.build_schema()
    print(x)
