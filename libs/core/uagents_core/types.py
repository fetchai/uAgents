from pydantic import BaseModel
from typing import Literal

JsonStr = str

AgentType = Literal["mailbox", "proxy", "custom"]


class AgentEndpoint(BaseModel):
    url: str
    weight: int
