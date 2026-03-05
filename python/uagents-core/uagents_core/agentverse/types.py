from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel

from uagents_core.types import AgentEndpoint

AgentStatus = Literal["active", "inactive", "offline"]
AgentType = Literal["hosted", "mailbox", "custom", "local", "proxy"]


class AgentProtocol(BaseModel):
    name: str
    version: str
    digest: str


class AlmanacRegistration(BaseModel):
    expiry: datetime
    status: AgentStatus
    type: AgentType
    metadata: Dict[str, Any] | None
    protocols: List[str]
    endpoints: List[AgentEndpoint]
    domain_name: str | None


class SearchRecord(BaseModel):
    status: AgentStatus
    type: AgentType
    metadata: Dict[str, Any] | None
    protocols: List[AgentProtocol]
    domain: str | None

    name: str
    description: str
    readme: str
    avatar_href: str | None
    handle: str | None

    created_at: datetime
    last_updated: datetime

    total_interactions: int
