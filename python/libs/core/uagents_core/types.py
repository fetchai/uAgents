from typing import Literal

from pydantic import BaseModel

JsonStr = str

AgentType = Literal["mailbox", "proxy", "custom"]

AddressPrefix = Literal["agent", "test-agent"]


class AgentEndpoint(BaseModel):
    url: str
    weight: int
