import logging

from uagents_core.config import AgentverseConfig
from uagents_core.types import AgentEndpoint

from uagents.utils import get_logger

AGENT_PREFIX = "agent"
LEDGER_PREFIX = "fetch"
USER_PREFIX = "user"
TESTNET_PREFIX = "test-agent"
MAINNET_PREFIX = "agent"
AGENT_ADDRESS_LENGTH = 65

MAINNET_CONTRACT_ALMANAC = (
    "fetch1mezzhfj7qgveewzwzdk6lz5sae4dunpmmsjr9u7z0tpmdsae8zmquq3y0y"
)
TESTNET_CONTRACT_ALMANAC = (
    "fetch1tjagw8g8nn4cwuw00cf0m5tl4l6wfw9c0ue507fhx9e3yrsck8zs0l3q4w"
)
MAINNET_CONTRACT_NAME_SERVICE = (
    "fetch1479lwv5vy8skute5cycuz727e55spkhxut0valrcm38x9caa2x8q99ef0q"
)
TESTNET_CONTRACT_NAME_SERVICE = (
    "fetch1mxz8kn3l5ksaftx8a9pj9a6prpzk2uhxnqdkwuqvuh37tw80xu6qges77l"
)
TESTNET_REGISTRATION_FEE = 500000000000000000
REGISTRATION_UPDATE_INTERVAL_SECONDS = 3600
REGISTRATION_RETRY_INTERVAL_SECONDS = 60
AVERAGE_BLOCK_INTERVAL = 6
DEFAULT_LEDGER_TX_WAIT_SECONDS = 30
ALMANAC_CONTRACT_VERSION = "2.2.0"

AGENTVERSE_BASE_URL = "agentverse.ai"
AGENTVERSE_HTTP_PREFIX = "https"
AGENTVERSE_URL = AGENTVERSE_HTTP_PREFIX + "://" + AGENTVERSE_BASE_URL
ALMANAC_API_URL = AGENTVERSE_URL + "/v1/almanac"

ALMANAC_API_TIMEOUT_SECONDS = 1.0
ALMANAC_API_MAX_RETRIES = 10
ALMANAC_REGISTRATION_WAIT = 100
MAILBOX_POLL_INTERVAL_SECONDS = 1.0

ORACLE_AGENT_DOMAIN = "verify.fetch.ai"
ANAME_REGISTRATION_SECONDS = 5184000

WALLET_MESSAGING_POLL_INTERVAL_SECONDS = 2.0

RESPONSE_TIME_HINT_SECONDS = 5
DEFAULT_ENVELOPE_TIMEOUT_SECONDS = 30
DEFAULT_MAX_ENDPOINTS = 10
DEFAULT_SEARCH_LIMIT = 100

MESSAGE_HISTORY_MESSAGE_LIMIT = 1000
MESSAGE_HISTORY_RETENTION_SECONDS = 86400


def parse_endpoint_config(
    endpoint: str | list[str] | dict[str, dict] | None,
    agentverse: AgentverseConfig,
    mailbox: bool = False,
    proxy: bool = False,
    logger: logging.Logger | None = None,
) -> list[AgentEndpoint]:
    """
    Parse the user-provided endpoint configuration.

    Args:
        endpoint (str | list[str] | dict[str, dict] | None): The endpoint configuration.
        agentverse (AgentverseConfig): The agentverse configuration.
        mailbox (bool): Whether to use the mailbox endpoint.
        proxy (bool): Whether to use the proxy endpoint.
        logger (logging.Logger | None): The logger to use.

    Returns:
        [list[AgentEndpoint]: The parsed endpoint configuration.
    """
    logger = logger or get_logger("config")

    if endpoint:
        if mailbox:
            logger.warning("Endpoint configuration overrides mailbox setting.")
        if proxy:
            logger.warning("Endpoint configuration overrides proxy setting.")
    elif mailbox and proxy:
        logger.warning(
            "Mailbox and proxy settings are mutually exclusive. Defaulting to mailbox."
        )

    if isinstance(endpoint, dict):
        endpoints = [
            AgentEndpoint.model_validate(
                {"url": val[0], "weight": val[1].get("weight") or 1}
            )
            for val in endpoint.items()
        ]
    elif isinstance(endpoint, list):
        endpoints = [
            AgentEndpoint.model_validate({"url": val, "weight": 1}) for val in endpoint
        ]
    elif isinstance(endpoint, str):
        endpoints = [AgentEndpoint.model_validate({"url": endpoint, "weight": 1})]
    elif mailbox:
        endpoints = [AgentEndpoint(url=f"{agentverse.url}/v1/submit", weight=1)]
    elif proxy:
        endpoints = [AgentEndpoint(url=f"{agentverse.url}/v1/proxy/submit", weight=1)]
    else:
        endpoints = []
    return endpoints


def parse_agentverse_config(
    config: str | dict[str, str] | None = None,
) -> AgentverseConfig:
    """
    Parse the user-provided agentverse configuration.

    Returns:
        AgentverseConfig: The parsed agentverse configuration.
    """
    base_url = AGENTVERSE_BASE_URL
    protocol = None
    protocol_override = None

    if isinstance(config, str):
        if config.count("@") == 1:
            _, base_url = config.split("@")
        elif "://" in config:
            base_url = config
    elif isinstance(config, dict):
        base_url = config.get("base_url") or base_url
        proto = config.get("protocol")
        protocol_override = proto if proto in {"http", "https"} else None

    if "://" in base_url:
        protocol, base_url = base_url.split("://")
    http_prefix = protocol_override or protocol or "https"

    return AgentverseConfig(
        base_url=base_url,
        http_prefix=http_prefix,
    )
