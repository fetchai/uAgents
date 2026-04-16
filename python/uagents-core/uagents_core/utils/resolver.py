"""This module provides methods to resolve an agent address."""

import urllib.parse
import ipaddress
import socket
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
from uagents_core.types import Domain, Resolver

logger = get_logger("uagents_core.utils.resolver")


def is_safe_url(url: str) -> bool:
    """
    Check if a URL is safe for an agent to connect to.
    Prevents SSRF by blocking private/internal IP addresses and cloud metadata.
    """
    try:
        parsed_url = urllib.parse.urlsplit(url)
        hostname = parsed_url.hostname
        if not hostname:
            return False

        # Block common local hostnames
        if hostname.lower() in ["localhost", "127.0.0.1", "::1"]:
            return False

        # Check if hostname is an IP address
        try:
            ip = ipaddress.ip_address(hostname)
            # is_private covers RFC 1918 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
            # it also covers loopback and link-local (169.254.0.0/16)
            return not (ip.is_private or ip.is_loopback or ip.is_link_local)
        except ValueError:
            # If not an IP address, resolve hostname to check IPs
            # Note: This doesn't prevent DNS Rebinding, but adds a basic layer
            try:
                # Basic check: hostname shouldn't resolve to a private IP
                addr_info = socket.getaddrinfo(hostname, None)
                for info in addr_info:
                    ip_str = info[4][0]
                    ip = ipaddress.ip_address(ip_str)
                    if ip.is_private or ip.is_loopback or ip.is_link_local:
                        return False
            except socket.gaierror:
                # If resolution fails, we let it pass for now as the request will fail anyway
                pass

        return True
    except Exception:
        return False


def lookup_address_for_domain(
    agent_identifier: str,
    *,
    agentverse_config: AgentverseConfig | None = None,
) -> str | None:
    agentverse_config = agentverse_config or AgentverseConfig()
    almanac_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_ALMANAC_API_PATH)

    prefix, domain, _ = parse_identifier(agent_identifier)
    if not domain:
        logger.error(
            "No domain provided in agent identifier",
            extra={"identifier": agent_identifier},
        )
        return None

    params = {"prefix": prefix} if prefix else None
    try:
        response = requests.get(
            url=f"{almanac_api}/domains/{domain}",
            timeout=DEFAULT_REQUEST_TIMEOUT,
            params=params,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(
            msg="Error looking up domain",
            extra={"domain": domain, "exception": str(e)},
        )
        return None

    domain_record = Domain.model_validate(response.json())

    agent_records = domain_record.assigned_agents
    if len(agent_records) == 0:
        return None
    elif len(agent_records) == 1:
        return agent_records[0].address
    else:
        addresses = [val.address for val in agent_records]
        weights = [val.weight for val in agent_records]
        return weighted_random_sample(addresses, weights=weights, k=1)[0]


def lookup_endpoint_for_agent(
    agent_identifier: str,
    *,
    max_endpoints: int = DEFAULT_MAX_ENDPOINTS,
    agentverse_config: AgentverseConfig | None = None,
) -> list[str]:
    \"\"\"
    Resolve the endpoints for an agent using the Almanac API.

    Args:
        destination (str): The destination address to look up.

    Returns:
        List[str]: The endpoint(s) for the agent.
    \"\"\"

    agentverse_config = agentverse_config or AgentverseConfig()
    almanac_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_ALMANAC_API_PATH)

    prefix, domain, agent_address = parse_identifier(agent_identifier)

    if not agent_address:
        if domain:
            agent_address = lookup_address_for_domain(
                agent_identifier=agent_identifier,
                agentverse_config=agentverse_config,
            )
        else:
            logger.error(
                "No address or domain provided in identifier",
                extra={"identifier": agent_identifier},
            )
            return []

    request_meta: dict[str, Any] = {
        "agent_address": agent_address,
        "lookup_url": almanac_api,
    }
    logger.debug(msg="looking up endpoint for agent", extra=request_meta)
    try:
        params = {"prefix": prefix} if prefix else None
        response = requests.get(
            url=f"{almanac_api}/agents/{agent_address}",
            params=params,
            timeout=DEFAULT_REQUEST_TIMEOUT,
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
        safe_endpoints = []
        for val in endpoints:
            url = val.get("url")
            if is_safe_url(url):
                safe_endpoints.append(val)
            else:
                logger.warning(
                    "Skipping unsafe endpoint",
                    extra={"agent_address": agent_address, "url": url},
                )

        if len(safe_endpoints) == 0:
            return []

        urls = [val.get("url") for val in safe_endpoints]
        weights = [val.get("weight") for val in safe_endpoints]
        return weighted_random_sample(
            items=urls,
            weights=weights,
            k=min(max_endpoints, len(safe_endpoints)),
        )

    return []


class AlmanacResolver(Resolver):
    def __init__(
        self, max_endpoints: int = 1, agentverse_config: AgentverseConfig | None = None
    ):
        self.agentverse_config = agentverse_config or AgentverseConfig()
        self.max_endpoints = max_endpoints

    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        endpoints = lookup_endpoint_for_agent(
            agent_identifier=destination,
            max_endpoints=self.max_endpoints,
            agentverse_config=self.agentverse_config,
        )
        return None, endpoints

    def sync_resolve(self, destination: str) -> list[str]:
        endpoints = lookup_endpoint_for_agent(
            agent_identifier=destination,
            max_endpoints=self.max_endpoints,
            agentverse_config=self.agentverse_config,
        )
        return endpoints
