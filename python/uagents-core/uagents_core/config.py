from pydantic import BaseModel

DEFAULT_AGENTVERSE_URL = "agentverse.ai"
DEFAULT_ALMANAC_API_PATH = "/v1/almanac"
DEFAULT_REGISTRATION_PATH = "/v1/agents"
DEFAULT_CHALLENGE_PATH = "/v1/auth/challenge"
DEFAULT_MAILBOX_PATH = "/v1/submit"
DEFAULT_PROXY_PATH = "/v1/proxy/submit"
DEFAULT_STORAGE_PATH = "/v1/storage"

DEFAULT_MAX_ENDPOINTS = 10

DEFAULT_REQUEST_TIMEOUT = 10

AGENT_ADDRESS_LENGTH = 65
AGENT_PREFIX = "agent"


class AgentverseConfig(BaseModel):
    base_url: str = DEFAULT_AGENTVERSE_URL
    http_prefix: str = "https"

    @property
    def url(self) -> str:
        return f"{self.http_prefix}://{self.base_url}"

    @property
    def mailbox_endpoint(self) -> str:
        return f"{self.url}{DEFAULT_MAILBOX_PATH}"

    @property
    def proxy_endpoint(self) -> str:
        return f"{self.url}{DEFAULT_PROXY_PATH}"

    @property
    def storage_endpoint(self) -> str:
        return f"{self.url}{DEFAULT_STORAGE_PATH}"
