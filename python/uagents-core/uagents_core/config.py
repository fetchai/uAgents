from pydantic import BaseModel

DEFAULT_AGENTVERSE_URL = "agentverse.ai"
DEFAULT_ALMANAC_API_PATH = "/v1/almanac"
DEFAULT_REGISTRATION_PATH = "/v2/agents"
DEFAULT_IDENTITY_PATH = "/v2/identity"
DEFAULT_MAILBOX_PATH = "/v2/agents/mailbox/submit"
DEFAULT_PROXY_PATH = "/v2/agents/proxy/submit"
DEFAULT_STORAGE_PATH = "/v1/storage"
DEFAULT_PAYMENTS_PATH = "/v1/payments"
DEFAULT_SEARCH_PATH = "/v1/search"

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
    def storage_api(self) -> str:
        return f"{self.url}{DEFAULT_STORAGE_PATH}"

    @property
    def payments_api(self) -> str:
        return f"{self.url}{DEFAULT_PAYMENTS_PATH}"

    @property
    def almanac_api(self) -> str:
        return f"{self.url}{DEFAULT_ALMANAC_API_PATH}"

    @property
    def agents_api(self) -> str:
        return f"{self.url}{DEFAULT_REGISTRATION_PATH}"

    @property
    def identity_api(self) -> str:
        return f"{self.url}{DEFAULT_IDENTITY_PATH}"

    @property
    def search_api(self) -> str:
        return f"{self.url}{DEFAULT_SEARCH_PATH}"
