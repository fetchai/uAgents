from pydantic import BaseModel

DEFAULT_AGENTVERSE_URL = "agentverse.ai"
DEFAULT_ALMANAC_API_PATH = "/v1/almanac"
DEFAULT_REGISTRATION_PATH = "/v1/agents"
DEFAULT_CHALLENGE_PATH = "/v1/auth/challenge"

DEFAULT_MAX_ENDPOINTS = 10

AGENT_ADDRESS_LENGTH = 65
AGENT_PREFIX = "agent"


class AgentverseConfig(BaseModel):
    base_url: str = DEFAULT_AGENTVERSE_URL
    protocol: str = "https"
    http_prefix: str = "https"

    @property
    def url(self) -> str:
        return f"{self.http_prefix}://{self.base_url}"
