"""Endpoint Resolver."""

import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from uagents.config import (
    AGENT_ADDRESS_LENGTH,
    AGENT_PREFIX,
    ALMANAC_API_URL,
    DEFAULT_MAX_ENDPOINTS,
    MAINNET_PREFIX,
    TESTNET_PREFIX,
)
from uagents.crypto import is_user_address
from uagents.network import get_almanac_contract, get_name_service_contract
from uagents.utils import get_logger

LOGGER = get_logger("resolver", logging.WARNING)


def weighted_random_sample(
    items: List[Any], weights: Optional[List[float]] = None, k: int = 1, rng=random
) -> List[Any]:
    """
    Weighted random sample from a list of items without replacement.

    Ref: Efraimidis, Pavlos S. "Weighted random sampling over data streams."

    Args:
        items (List[Any]): The list of items to sample from.
        weights (Optional[List[float]]): The optional list of weights for each item.
        k (int): The number of items to sample.
        rng (random): The random number generator.

    Returns:
        List[Any]: The sampled items.
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


def parse_identifier(identifier: str) -> Tuple[str, str, str]:
    """
    Parse an agent identifier string into prefix, name, and address.

    Args:
        identifier (str): The identifier string to be parsed.

    Returns:
        Tuple[str, str, str]: A tuple containing the prefix, name, and address as strings.
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


def query_record(agent_address: str, service: str, test: bool) -> dict:
    """
    Query a record from the Almanac contract.

    Args:
        agent_address (str): The address of the agent.
        service (str): The type of service to query.

    Returns:
        dict: The query result.
    """
    contract = get_almanac_contract(test)
    query_msg = {
        "query_record": {"agent_address": agent_address, "record_type": service}
    }
    result = contract.query(query_msg)
    return result


def get_agent_address(name: str, test: bool) -> Optional[str]:
    """
    Get the agent address associated with the provided name from the name service contract.

    Args:
        name (str): The name to query.
        test (bool): Whether to use the testnet or mainnet contract.

    Returns:
        Optional[str]: The associated agent address if found.
    """
    query_msg = {"domain_record": {"domain": f"{name}"}}
    result = get_name_service_contract(test).query(query_msg)
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
    # pylint: disable=unnecessary-pass
    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination to an address and endpoint.

        Args:
            destination (str): The destination name or address to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.
        """
        pass


class GlobalResolver(Resolver):
    def __init__(
        self, max_endpoints: Optional[int] = None, almanac_api_url: Optional[str] = None
    ):
        """
        Initialize the GlobalResolver.

        Args:
            max_endpoints (Optional[int]): The maximum number of endpoints to return.
            almanac_api_url (Optional[str]): The url for almanac api
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanac_api_resolver = AlmanacApiResolver(
            max_endpoints=self._max_endpoints, almanac_api_url=almanac_api_url
        )
        self._name_service_resolver = NameServiceResolver(
            max_endpoints=self._max_endpoints
        )

    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the appropriate resolver.

        Args:
            destination (str): The destination name or address to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.
        """

        prefix, _, address = parse_identifier(destination)

        if is_valid_prefix(prefix):
            resolver = (
                self._almanac_api_resolver if address else self._name_service_resolver
            )
            return await resolver.resolve(destination)

        return None, []


class AlmanacContractResolver(Resolver):
    def __init__(self, max_endpoints: Optional[int] = None):
        """
        Initialize the AlmanacContractResolver.

        Args:
            max_endpoints (Optional[int]): The maximum number of endpoints to return.
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS

    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the Almanac contract.

        Args:
            destination (str): The destination address to resolve.

        Returns:
            Tuple[str, List[str]]: The address and resolved endpoints.
        """
        prefix, _, address = parse_identifier(destination)
        is_testnet = prefix != MAINNET_PREFIX
        result = query_record(address, "service", is_testnet)
        if result is not None:
            record = result.get("record") or {}
            endpoint_list = (
                record.get("record", {}).get("service", {}).get("endpoints", [])
            )

            if len(endpoint_list) > 0:
                endpoints = [val.get("url") for val in endpoint_list]
                weights = [val.get("weight") for val in endpoint_list]
                return address, weighted_random_sample(
                    endpoints,
                    weights=weights,
                    k=min(self._max_endpoints, len(endpoints)),
                )

        return None, []


class AlmanacApiResolver(Resolver):
    def __init__(
        self, max_endpoints: Optional[int] = None, almanac_api_url: Optional[str] = None
    ):
        """
        Initialize the AlmanacApiResolver.

        Args:
            max_endpoints (Optional[int]): The maximum number of endpoints to return.
            almanac_api_url (Optional[str]): The url for almanac api
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanac_api_url = almanac_api_url or ALMANAC_API_URL
        self._almanac_contract_resolver = AlmanacContractResolver(
            max_endpoints=self._max_endpoints
        )

    async def _api_resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the Almanac API.

        Args:
            destination (str): The destination address to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address and resolved endpoints.
        """
        try:
            _, _, address = parse_identifier(destination)
            response = requests.get(f"{self._almanac_api_url}agents/{address}")

            if response.status_code != 200:
                if response.status_code != 404:
                    LOGGER.warning(
                        f"Failed to resolve agent {address} from {self._almanac_api_url},"
                        f"querying Almanac contract..."
                    )
                return None, []

            agent = response.json()

            expiry_str = agent.get("expiry", None)
            if expiry_str is None:
                return None, []

            expiry = datetime.fromisoformat(expiry_str)
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

    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the Almanac API.
        If the resolution using API fails, it retries using the Almanac Contract.

        Args:
            destination (str): The destination address to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address and resolved endpoints.
        """
        address, endpoints = await self._api_resolve(destination)
        return (
            (address, endpoints)
            if address is not None
            else await self._almanac_contract_resolver.resolve(destination)
        )


class NameServiceResolver(Resolver):
    def __init__(self, max_endpoints: Optional[int] = None):
        """
        Initialize the NameServiceResolver.

        Args:
            max_endpoints (Optional[int]): The maximum number of endpoints to return.
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanac_api_resolver = AlmanacApiResolver(
            max_endpoints=self._max_endpoints
        )

    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the NameService contract.

        Args:
            destination (str): The destination name to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.
        """
        prefix, name, _ = parse_identifier(destination)
        use_testnet = prefix != MAINNET_PREFIX
        address = get_agent_address(name, use_testnet)
        if address is not None:
            return await self._almanac_api_resolver.resolve(address)
        return None, []


class RulesBasedResolver(Resolver):
    def __init__(self, rules: Dict[str, str], max_endpoints: Optional[int] = None):
        """
        Initialize the RulesBasedResolver with the provided rules.

        Args:
            rules (Dict[str, str]): A dictionary of rules mapping destinations to endpoints.
            max_endpoints (Optional[int]): The maximum number of endpoints to return.
        """
        self._rules = rules
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS

    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the provided rules.

        Args:
            destination (str): The destination to resolve.

        Returns:
            Tuple[str, List[str]]: The address and resolved endpoints.
        """
        endpoints = self._rules.get(destination)
        if isinstance(endpoints, str):
            endpoints = [endpoints]
        elif endpoints is None:
            endpoints = []
        if len(endpoints) > self._max_endpoints:
            endpoints = random.sample(
                endpoints, k=min(self._max_endpoints, len(endpoints))
            )
        return destination, endpoints
