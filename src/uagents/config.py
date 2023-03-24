import logging
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from uvicorn.logging import DefaultFormatter

logging.basicConfig(level=logging.INFO)


class AgentNetwork(Enum):
    FETCHAI_TESTNET = 1
    FETCHAI_MAINNET = 2


AGENT_PREFIX = "agent"
LEDGER_PREFIX = "fetch"
USER_PREFIX = "user"
CONTRACT_ALMANAC = "fetch1h5rhtj5m6dqjmufj5m3t4mq6l7cnd8dvaxclwmrk6tfdm0gy3lmszksf0s"
CONTRACT_SERVICE = "fetch1yrf4xpglq02fzj50m9wn44qdq89a5vr0ufa42qa506uhwal4n79s99sp87"
REGISTRATION_FEE = 500000000000000000
REGISTRATION_DENOM = "atestfet"
BLOCK_INTERVAL = 5
AGENT_NETWORK = AgentNetwork.FETCHAI_TESTNET

MAILBOX_SERVER_URL = "127.0.0.1:8000"
MAILBOX_POLL_INTERVAL_SECONDS = 1.0

DEFAULT_ENVELOPE_TIMEOUT_SECONDS = 30


def parse_endpoint_config(
    endpoint: Optional[Union[List[str], Dict[str, dict]]]
) -> List[Dict[str, Any]]:
    if isinstance(endpoint, dict):
        endpoints = [
            {"url": val[0], "weight": val[1].get("weight") or 1}
            for val in endpoint.items()
        ]
    elif isinstance(endpoint, list):
        endpoints = [{"url": val, "weight": 1} for val in endpoint]
    else:
        endpoints = None
    return endpoints


def parse_mailbox_config(mailbox: Union[str, Dict[str, str]]) -> Dict[str, str]:
    api_key = None
    base_url = MAILBOX_SERVER_URL
    if isinstance(mailbox, str):
        if mailbox.count("@") == 1:
            api_key, base_url = mailbox.split("@")
        else:
            api_key = mailbox
    elif isinstance(mailbox, dict):
        api_key = mailbox.get("api_key")
        base_url = mailbox.get("base_url")
        protocol = mailbox.get("protocol") or "http"
    if "://" in base_url:
        protocol, base_url = base_url.split("://")
    else:
        protocol = "wss"
    http_prefix = "https" if protocol in {"wss", "https"} else "http"
    return {
        "api_key": api_key,
        "base_url": base_url,
        "protocol": protocol,
        "http_prefix": http_prefix,
    }


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setFormatter(
        DefaultFormatter(fmt="%(levelprefix)s [%(name)5s]: %(message)s")
    )
    logger.addHandler(log_handler)
    logger.propagate = False
    return logger
