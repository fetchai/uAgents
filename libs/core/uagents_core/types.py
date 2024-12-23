from pydantic import BaseModel
from typing import Literal


AgentType = Literal["mailbox", "proxy", "custom"]


class AgentEndpoint(BaseModel):
    url: str
    weight: int
