"""This module provides methods to resolve an agent address."""

import urllib.parse
from typing import Any

import requests

from uagents_core.config import (
    DEFAULT_ALMANAC_API_PATH,
    DEFAULT_MAX_ENDPOINTS,
    DEFAULT_REQUEST_TIMEOUT,
    AgentverseConfig,
)
from uagents_core.helpers import weighted_random_sample
from uagents_core.identity import parse_identifier
from uagents_core.logger import get_logger

logger = get_logger("uagents_core.utils.resolver")


def lookup_endpoint_for_agent(
    agent_identifier: str,
    *,
    max_endpoints: int = DEFAULT_MAX_ENDPOINTS,
    agentverse_config: AgentverseConfig | None = None,
) -> list[str]:
    """
    Resolve the endpoints for an agent using the Almanac API.

    Args:
        destination (str): The destination address to look up.

    Returns:
        List[str]: The endpoint(s) for the agent.
    """
    _, _, agent_address = parse_identifier(agent_identifier)

    agentverse_config = agentverse_config or AgentverseConfig()
    almanac_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_ALMANAC_API_PATH)

    request_meta: dict[str, Any] = {
        "agent_address": agent_address,
        "lookup_url": almanac_api,
    }
    logger.debug(msg="looking up endpoint for agent", extra=request_meta)
    try:
        response = requests.get(
            url=f"{almanac_api}/agents/{agent_address}", timeout=DEFAULT_REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.RequestException as e:
        request_meta["exception"] = e
        logger.error(msg="Error looking up agent endpoint", extra=request_meta)
        return []

    request_meta["response_status"] = response.status_code
    logger.info(
        msg="Got response looking up agent endpoint",
        extra=request_meta,
    )

    endpoints: list = response.json().get("endpoints", [])

    if len(endpoints) > 0:
        urls = [val.get("url") for val in endpoints]
        weights = [val.get("weight") for val in endpoints]
        return weighted_random_sample(
            items=urls,
            weights=weights,
            k=min(max_endpoints, len(endpoints)),
        )

    return []
