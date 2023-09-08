"""Endpoint Resolver."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import random

from uagents.config import DEFAULT_MAX_ENDPOINTS
from uagents.network import get_almanac_contract, get_name_service_contract


def query_record(agent_address: str, service: str) -> dict:
    """
    Query a record from the Almanac contract.

    Args:
        agent_address (str): The address of the agent.
        service (str): The type of service to query.

    Returns:
        dict: The query result.
    """
    contract = get_almanac_contract()
    query_msg = {
        "query_record": {"agent_address": agent_address, "record_type": service}
    }
    result = contract.query(query_msg)
    return result


def get_agent_address(name: str) -> str:
    """
    Get the agent address associated with the provided name from the name service contract.

    Args:
        name (str): The name to query.

    Returns:
        Optional[str]: The associated agent address if found.
    """
    query_msg = {"domain_record": {"domain": f"{name}"}}
    result = get_name_service_contract().query(query_msg)
    if result["record"] is not None:
        registered_address = result["record"]["records"][0]["agent_address"]["records"]
        if len(registered_address) > 0:
            return registered_address[0]["address"]
    return None


def is_agent_address(address):
    """
    Check if the provided address is a valid agent address.

    Args:
        address: The address to check.

    Returns:
        bool: True if the address is a valid agent address, False otherwise.
    """
    if not isinstance(address, str):
        return False

    prefix = "agent"
    expected_length = 65

    return address.startswith(prefix) and len(address) == expected_length


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
    def __init__(self):
        """Initialize the GlobalResolver."""
        self._almanc_resolver = AlmanacResolver()
        self._name_service_resolver = NameServiceResolver()

    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the appropriate resolver.

        Args:
            destination (str): The destination name or address to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.
        """
        if is_agent_address(destination):
            return await self._almanc_resolver.resolve(destination)
        return await self._name_service_resolver.resolve(destination)


class AlmanacResolver(Resolver):
    async def resolve(
        self, destination: str, max_endpoints: Optional[int] = DEFAULT_MAX_ENDPOINTS
    ) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the Almanac contract.

        Args:
            destination (str): The destination address to resolve.

        Returns:
            Tuple[str, List[str]]: The address and resolved endpoints.
        """
        result = query_record(destination, "service")
        if result is not None:
            record = result.get("record") or {}
            endpoint_list = (
                record.get("record", {}).get("service", {}).get("endpoints", [])
            )

            if len(endpoint_list) > 0:
                endpoints = [val.get("url") for val in endpoint_list]
                weights = [val.get("weight") for val in endpoint_list]
                return destination, random.choices(
                    endpoints, weights=weights, k=max_endpoints
                )

        return None, []


class NameServiceResolver(Resolver):
    def __init__(self):
        """Initialize the NameServiceResolver."""
        self._almanac_resolver = AlmanacResolver()

    async def resolve(self, destination: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve the destination using the NameService contract.

        Args:
            destination (str): The destination name to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.
        """
        address = get_agent_address(destination)
        if address is not None:
            return await self._almanac_resolver.resolve(address)
        return None, []


class RulesBasedResolver(Resolver):
    def __init__(self, rules: Dict[str, str]) -> Tuple[Optional[str], List[str]]:
        """
        Initialize the RulesBasedResolver with the provided rules.

        Args:
            rules (Dict[str, str]): A dictionary of rules mapping destinations to endpoints.
        """
        self._rules = rules

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
        return destination, endpoints
