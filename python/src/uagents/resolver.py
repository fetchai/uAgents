"""Endpoint Resolver."""

import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import requests
from dateutil import parser
from uagents_core.crypto import is_user_address

from uagents.config import (
    AGENT_ADDRESS_LENGTH,
    AGENT_PREFIX,
    ALMANAC_API_URL,
    DEFAULT_MAX_ENDPOINTS,
    MAINNET_PREFIX,
    TESTNET_PREFIX,
)
from uagents.network import (
    AlmanacContract,
    get_almanac_contract,
    get_name_service_contract,
)
from uagents.types import AgentNetwork
from uagents.utils import get_logger

LOGGER: logging.Logger = get_logger("resolver", logging.WARNING)


def weighted_random_sample(
    items: list[Any], weights: list[float] | None = None, k: int = 1, rng=random
) -> list[Any]:
    """
    Weighted random sample from a list of items without replacement.

    Ref: Efraimidis, Pavlos S. "Weighted random sampling over data streams."

    Args:
        items (list[Any]): The list of items to sample from.
        weights (list[float]] | None) The optional list of weights for each item.
        k (int): The number of items to sample.
        rng (random): The random number generator.

    Returns:
        list[Any]: The sampled items.
    """
    if weights is None:
        return rng.sample(items, k=k)
    values = [rng.random() ** (1 / w) for w in weights]
    order = sorted(range(len(items)), key=lambda i: values[i])
    return [items[i] for i in order[-k:]]


def is_valid_address(address: str) -> bool:
    """
    Check if the given string is a valid address.

    Args:
        address (str): The address to be checked.

    Returns:
        bool: True if the address is valid; False otherwise.
    """
    return is_user_address(address) or (
        len(address) == AGENT_ADDRESS_LENGTH and address.startswith(AGENT_PREFIX)
    )


def is_valid_prefix(prefix: str) -> bool:
    """
    Check if the given string is a valid prefix.

    Args:
        prefix (str): The prefix to be checked.

    Returns:
        bool: True if the prefix is valid; False otherwise.
    """
    valid_prefixes = [TESTNET_PREFIX, MAINNET_PREFIX, ""]
    return prefix in valid_prefixes


def parse_prefix(prefix: str) -> AgentNetwork:
    """
    Parse an agent prefix string into the corresponding network.

    Args:
        prefix (str): The prefix string to be parsed.

    Returns:
        AgentNetwork: The corresponding network.
    """
    if prefix in (TESTNET_PREFIX, ""):
        return "testnet"
    if prefix == MAINNET_PREFIX:
        return "mainnet"
    raise ValueError(f"Invalid prefix: {prefix}")


def parse_identifier(identifier: str) -> tuple[str, str, str]:
    """
    Parse an agent identifier string into prefix, name, and address.

    Args:
        identifier (str): The identifier string to be parsed.

    Returns:
        tuple[str, str, str]: A tuple containing the prefix, name, and address as strings.
    """

    prefix = ""
    name = ""
    address = ""

    if "://" in identifier:
        prefix, identifier = identifier.split("://", 1)

    if "/" in identifier:
        name, identifier = identifier.split("/", 1)

    if is_valid_address(identifier):
        address = identifier
    else:
        name = identifier

    return prefix, name, address


def query_record(agent_address: str, service: str, network: AgentNetwork) -> dict:
    """
    Query a record from the Almanac contract.

    Args:
        agent_address (str): The address of the agent.
        service (str): The type of service to query.
        network (AgentNetwork): The network to query (mainnet or testnet).

    Returns:
        dict: The query result.
    """
    contract: AlmanacContract | None = get_almanac_contract(network)
    if not contract:
        raise ValueError("Almanac contract not found.")
    query_msg = {
        "query_record": {"agent_address": agent_address, "record_type": service}
    }
    result = contract.query(query_msg)
    return result


def get_agent_address(name: str, network: AgentNetwork) -> str | None:
    """
    Get the agent address associated with the provided name from the name service contract.

    Args:
        name (str): The name to query.
        network (AgentNetwork): The network to query (mainnet or testnet).

    Returns:
        str | None: The associated agent address if found.
    """
    query_msg = {"query_domain_record": {"domain": f"{name}"}}
    result = get_name_service_contract(network).query(query_msg)
    if result["record"] is not None:
        registered_records = result["record"]["records"][0]["agent_address"]["records"]
        if len(registered_records) > 0:
            addresses = [val.get("address") for val in registered_records]
            weights = [val.get("weight") for val in registered_records]
            selected_address_list = weighted_random_sample(addresses, weights=weights)
            selected_address = (
                selected_address_list[0] if selected_address_list else None
            )
            return selected_address
    return None


class Resolver(ABC):
    @abstractmethod
    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination to an address and endpoint.

        Args:
            destination (str): The destination name or address to resolve.

        Returns:
            tuple[str | None, list[str]]: The address (if available) and resolved endpoints.
        """
        raise NotImplementedError


class GlobalResolver(Resolver):
    def __init__(
        self, max_endpoints: int | None = None, almanac_api_url: str | None = None
    ):
        """
        Initialize the GlobalResolver.

        Args:
            max_endpoints (int | None): The maximum number of endpoints to return.
            almanac_api_url (str | None): The url for almanac api
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanac_api_resolver = AlmanacApiResolver(
            max_endpoints=self._max_endpoints, almanac_api_url=almanac_api_url
        )
        self._name_service_resolver = NameServiceResolver(
            max_endpoints=self._max_endpoints
        )

    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination using the appropriate resolver.

        Args:
            destination (str): The destination name or address to resolve.

        Returns:
            tuple[str | None, list[str]]: The address (if available) and resolved endpoints.
        """

        prefix, _, address = parse_identifier(destination)

        if is_valid_prefix(prefix):
            resolver = (
                self._almanac_api_resolver if address else self._name_service_resolver
            )
            return await resolver.resolve(destination)

        return None, []


class AlmanacContractResolver(Resolver):
    def __init__(self, max_endpoints: int | None = None):
        """
        Initialize the AlmanacContractResolver.

        Args:
            max_endpoints (int | None): The maximum number of endpoints to return.
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS

    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination using the Almanac contract.

        Args:
            destination (str): The destination address to resolve.

        Returns:
            tuple[str | None, list[str]]: The address and resolved endpoints.
        """
        prefix, _, address = parse_identifier(destination)
        network = parse_prefix(prefix)
        result = query_record(agent_address=address, service="service", network=network)
        if result is not None:
            record = result.get("record") or {}
            endpoint_list = (
                record.get("record", {}).get("service", {}).get("endpoints", [])
            )

            if len(endpoint_list) > 0:
                endpoints = [val.get("url") for val in endpoint_list]
                weights = [val.get("weight") for val in endpoint_list]
                return address, weighted_random_sample(
                    items=endpoints,
                    weights=weights,
                    k=min(self._max_endpoints, len(endpoints)),
                )

        return None, []


class AlmanacApiResolver(Resolver):
    def __init__(
        self, max_endpoints: int | None = None, almanac_api_url: str | None = None
    ):
        """
        Initialize the AlmanacApiResolver.

        Args:
            max_endpoints (int | None): The maximum number of endpoints to return.
            almanac_api_url (str | None): The url for almanac api
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanac_api_url = almanac_api_url or ALMANAC_API_URL
        self._almanac_contract_resolver = AlmanacContractResolver(
            max_endpoints=self._max_endpoints
        )

    async def _api_resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination using the Almanac API.

        Args:
            destination (str): The destination address to resolve.

        Returns:
            tuple[str | None, list[str]]: The address and resolved endpoints.
        """
        try:
            _, _, address = parse_identifier(destination)
            response = requests.get(
                url=f"{self._almanac_api_url}/agents/{address}", timeout=5
            )

            if response.status_code != 200:
                if response.status_code != 404:
                    LOGGER.debug(
                        f"Failed to resolve agent {address} from {self._almanac_api_url}, "
                        "resolving via Almanac contract..."
                    )
                return None, []

            agent = response.json()

            expiry_str = agent.get("expiry", None)
            if expiry_str is None:
                return None, []

            expiry = parser.parse(expiry_str)
            current_time = datetime.now(timezone.utc)
            endpoint_list = agent.get("endpoints", [])

            if len(endpoint_list) > 0 and expiry > current_time:
                endpoints = [val.get("url") for val in endpoint_list]
                weights = [val.get("weight") for val in endpoint_list]
                return address, weighted_random_sample(
                    endpoints,
                    weights=weights,
                    k=min(self._max_endpoints, len(endpoints)),
                )
        except Exception as e:
            LOGGER.error(
                f"Error in AlmanacApiResolver when resolving {destination}: {e}"
            )

        return None, []

    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination using the Almanac API.
        If the resolution using API fails, it retries using the Almanac Contract.

        Args:
            destination (str): The destination address to resolve.

        Returns:
            tuple[str | None, list[str]]: The address and resolved endpoints.
        """
        address, endpoints = await self._api_resolve(destination)
        return (
            (address, endpoints)
            if address is not None
            else await self._almanac_contract_resolver.resolve(destination)
        )


class NameServiceResolver(Resolver):
    def __init__(self, max_endpoints: int | None = None):
        """
        Initialize the NameServiceResolver.

        Args:
            max_endpoints (int | None): The maximum number of endpoints to return.
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanac_api_resolver = AlmanacApiResolver(self._max_endpoints)

    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination using the NameService contract.

        Args:
            destination (str): The destination name to resolve.

        Returns:
            tuple[str | None, list[str]]: The address (if available) and resolved endpoints.
        """
        prefix, name, _ = parse_identifier(destination)
        network = parse_prefix(prefix)
        address = get_agent_address(name, network)
        if address is not None:
            return await self._almanac_api_resolver.resolve(address)
        return None, []


class RulesBasedResolver(Resolver):
    def __init__(self, rules: dict[str, str], max_endpoints: int | None = None):
        """
        Initialize the RulesBasedResolver with the provided rules.

        Args:
            rules (dict[str, str]): A dictionary of rules mapping destinations to endpoints.
            max_endpoints (int | None): The maximum number of endpoints to return.
        """
        self._rules = rules
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS

    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination using the provided rules.

        Args:
            destination (str): The destination to resolve.

        Returns:
            tuple[str | None, list[str]]: The address and resolved endpoints.
        """
        endpoints = self._rules.get(destination)
        if isinstance(endpoints, str):
            endpoints = [endpoints]
        elif endpoints is None:
            endpoints = []
        if len(endpoints) > self._max_endpoints:
            endpoints = random.sample(
                population=endpoints, k=min(self._max_endpoints, len(endpoints))
            )
        return destination, endpoints
