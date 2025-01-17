from typing import Optional
from pydantic import BaseModel, Field
from uagents_core.types import AgentType


class AgentUpdates(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    readme: Optional[str] = Field(default=None, max_length=80000)
    avatar_url: Optional[str] = Field(default=None, max_length=4000)
    agent_type: Optional[AgentType] = "custom"
