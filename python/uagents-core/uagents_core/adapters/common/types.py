from typing import Any
from urllib.parse import unquote, urlparse

from pydantic import BaseModel
from uagents_core.config import AgentverseConfig
from uagents_core.registration import AgentProfile


class AgentUri(BaseModel):
    key: str
    name: str
    agentverse_config: AgentverseConfig
    handle: str | None = None

    @classmethod
    def from_str(cls, uri: str) -> "AgentUri":
        parsed = urlparse(uri)

        if not parsed.scheme:
            raise ValueError("Scheme is missing.")
        if not parsed.hostname:
            raise ValueError("Hostname is missing.")
        if not parsed.username:
            raise ValueError("Agent handle is missing")
        if not parsed.password:
            raise ValueError("Agent key is missing.")
        if not parsed.path or len(parsed.path.split("/")) < 2:
            raise ValueError("Agent name is missing")

        name = unquote(parsed.path.split("/")[1])

        agentverse = AgentverseConfig(
            base_url=parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
            http_prefix=parsed.scheme,
        )

        return cls(
            key=parsed.password,
            name=name,
            agentverse_config=agentverse,
            handle=parsed.username,
        )


# TODO
class AgentOptions(BaseModel):
    verify_envelope: bool = True


class AgentverseAgent(BaseModel):
    uri: AgentUri
    profile: AgentProfile | None = None
    metadata: dict[str, Any] | None = None
    options: AgentOptions = AgentOptions()
