import logging
import sys


from typing import Any, Dict, List, Optional, Union

from uvicorn.logging import DefaultFormatter

logging.basicConfig(level=logging.INFO)


AGENT_PREFIX = "agent"
LEDGER_PREFIX = "fetch"
USER_PREFIX = "user"
TESTNET_PREFIX = "test-agent"
MAINNET_PREFIX = "agent"

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
REGISTRATION_FEE = 500000000000000000
REGISTRATION_DENOM = "atestfet"
REGISTRATION_UPDATE_INTERVAL_SECONDS = 3600
REGISTRATION_RETRY_INTERVAL_SECONDS = 60
AVERAGE_BLOCK_INTERVAL = 6

AGENTVERSE_URL = "https://agentverse.ai"
ALMANAC_API_URL = AGENTVERSE_URL + "/v1/almanac/"
MAILBOX_POLL_INTERVAL_SECONDS = 1.0

WALLET_MESSAGING_POLL_INTERVAL_SECONDS = 2.0

RESPONSE_TIME_HINT_SECONDS = 5
DEFAULT_ENVELOPE_TIMEOUT_SECONDS = 30
DEFAULT_MAX_ENDPOINTS = 10
DEFAULT_SEARCH_LIMIT = 100


def parse_endpoint_config(
    endpoint: Optional[Union[str, List[str], Dict[str, dict]]]
) -> List[Dict[str, Any]]:
    """
    Parse the user-provided endpoint configuration.

    Returns:
        List[Dict[str, Any]]: The parsed endpoint configuration.
    """
    if isinstance(endpoint, dict):
        endpoints = [
            {"url": val[0], "weight": val[1].get("weight") or 1}
            for val in endpoint.items()
        ]
    elif isinstance(endpoint, list):
        endpoints = [{"url": val, "weight": 1} for val in endpoint]
    elif isinstance(endpoint, str):
        endpoints = [{"url": endpoint, "weight": 1}]
    else:
        endpoints = None
    return endpoints


def parse_agentverse_config(
    config: Optional[Union[str, Dict[str, str]]] = None,
) -> Dict[str, str]:
    """
    Parse the user-provided agentverse configutation.

    Returns:
        Dict[str, str]: The parsed agentverse configuration.
    """
    agent_mailbox_key = None
    base_url = AGENTVERSE_URL
    protocol = None
    protocol_override = None
    if isinstance(config, str):
        if config.count("@") == 1:
            agent_mailbox_key, base_url = config.split("@")
        elif "://" in config:
            base_url = config
        else:
            agent_mailbox_key = config
    elif isinstance(config, dict):
        agent_mailbox_key = config.get("agent_mailbox_key")
        base_url = config.get("base_url") or base_url
        protocol_override = config.get("protocol")
    if "://" in base_url:
        protocol, base_url = base_url.split("://")
    protocol = protocol_override or protocol or "https"
    http_prefix = "https" if protocol in {"wss", "https"} else "http"
    return {
        "agent_mailbox_key": agent_mailbox_key,
        "base_url": base_url,
        "protocol": protocol,
        "http_prefix": http_prefix,
        "use_mailbox": agent_mailbox_key is not None,
    }


def get_logger(logger_name):
    """Get a logger with the given name using uvicorn's default formatter."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setFormatter(
        DefaultFormatter(fmt="%(levelprefix)s [%(name)5s]: %(message)s")
    )
    logger.addHandler(log_handler)
    logger.propagate = False
    return logger
