"""Endpoint Resolver."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import random

from uagents.config import (
    DEFAULT_MAX_ENDPOINTS,
    TESTNET_PREFIX,
    MAINNET_PREFIX,
    AGENT_PREFIX,
)
from uagents.network import get_almanac_contract, get_name_service_contract


def is_valid_address(address: str) -> bool:
    """
    Check if the given string is a valid address.

    Args:
        address (str): The address to be checked.

    Returns:
        bool: True if the address is valid; False otherwise.
    """
    return len(address) == 65 and address.startswith(AGENT_PREFIX)


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


def split_destination(destination: str) -> tuple:
    """
    Split a destination string into prefix and remainder.

    If the destination contains "://", it splits the prefix and remainder based on that.
    If not, it assumes an empty prefix and returns the entire destination as the remainder.

    Args:
        destination (str): The destination string to be split.

    Returns:
        tuple: A tuple containing the prefix and remainder as strings.
    """

    if "://" in destination:
        prefix, remainder = destination.split("://", 1)
        remainder = remainder.split("/", 1)[-1]
    else:
        return "", destination

    return prefix, remainder


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


def get_agent_address(name: str, test: bool) -> str:
    """
    Get the agent address associated with the provided name from the name service contract.

    Args:
        name (str): The name to query.

    Returns:
        Optional[str]: The associated agent address if found.
    """
    query_msg = {"domain_record": {"domain": f"{name}"}}
    result = get_name_service_contract(test).query(query_msg)
    if result["record"] is not None:
        registered_address = result["record"]["records"][0]["agent_address"]["records"]
        if len(registered_address) > 0:
            return registered_address[0]["address"]
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
    def __init__(self, max_endpoints: Optional[int] = None):
        """
        Initialize the GlobalResolver.

        Args:
            max_endpoints (Optional[int]): The maximum number of endpoints to return.
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanc_resolver = AlmanacResolver(max_endpoints=self._max_endpoints)
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

        prefix, remainder = split_destination(destination)

        if is_valid_prefix(prefix):
            resolver = (
                self._almanc_resolver
                if is_valid_address(remainder)
                else self._name_service_resolver
            )
            return await resolver.resolve(destination)

        return None, []


class AlmanacResolver(Resolver):
    def __init__(self, max_endpoints: Optional[int] = None):
        """
        Initialize the AlmanacResolver.

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
        prefix, address = split_destination(destination)
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
                return address, random.choices(
                    endpoints,
                    weights=weights,
                    k=min(self._max_endpoints, len(endpoints)),
                )

        return None, []


class NameServiceResolver(Resolver):
    def __init__(self, max_endpoints: Optional[int] = None):
        """
        Initialize the NameServiceResolver.

        Args:
            max_endpoints (Optional[int]): The maximum number of endpoints to return.
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanac_resolver = AlmanacResolver(max_endpoints=self._max_endpoints)

    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the NameService contract.

        Args:
            destination (str): The destination name to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.
        """
        prefix, name = split_destination(destination)
        is_testnet = prefix != MAINNET_PREFIX
        address = get_agent_address(name, is_testnet)
        if address is not None:
            return await self._almanac_resolver.resolve(address)
        return None, []


class RulesBasedResolver(Resolver):
    def __init__(
        self, rules: Dict[str, str], max_endpoints: Optional[int] = None
    ) -> Tuple[Optional[str], List[str]]:
        """
        Initialize the RulesBasedResolver with the provided rules.

        Args:
            rules (Dict[str, str]): A dictionary of rules mapping destinations to endpoints.
            max_endpoints (Optional[int]): The maximum number of endpoints to return.
        """
        self._rules = rules
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS

    async def resolve(self, destination: str) -> Optional[str]:
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
            endpoints = random.choices(
                endpoints, k=min(self._max_endpoints, len(endpoints))
            )
        return destination, endpoints
