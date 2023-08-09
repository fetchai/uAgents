"""Endpoint Resolver."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import random

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
        str: The associated agent address.
    """
    query_msg = {"domain_record": {"domain": f"{name}"}}
    result = get_name_service_contract().query(query_msg)
    if result["record"] is not None:
        registered_address = result["record"]["records"][0]["agent_address"]["records"]
        if len(registered_address) > 0:
            return registered_address[0]["address"]
        return 0
    return 1


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
    async def resolve(self, destination: str) -> Optional[str]:
        """
        Resolve the destination to an endpoint.

        Args:
            destination (str): The destination to resolve.

        Returns:
            Optional[str]: The resolved endpoint or None.
        """
        pass


class GlobalResolver(Resolver):
    async def resolve(self, destination: str) -> Optional[str]:
        """
        Resolve the destination using a combination of Almanac and NameService resolvers.

        Args:
            destination (str): The destination to resolve.

        Returns:
            Optional[str]: The resolved endpoint or None.
        """
        almanac_resolver = AlmanacResolver()
        name_service_resolver = NameServiceResolver()
        address = (
            destination
            if is_agent_address(destination)
            else await name_service_resolver.resolve(destination)
        )

        if is_agent_address(address):
            return await almanac_resolver.resolve(address)
        return None, None


class AlmanacResolver(Resolver):
    async def resolve(self, destination: str) -> Optional[str]:
        """
        Resolve the destination using the Almanac contract.

        Args:
            destination (str): The destination to resolve.

        Returns:
            Optional[str]: The resolved endpoint or None.
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
                return destination, random.choices(endpoints, weights=weights)[0]

        return None, None


class NameServiceResolver(Resolver):
    async def resolve(self, destination: str) -> Optional[str]:
        """
        Resolve the destination using the NameService contract.

        Args:
            destination (str): The destination to resolve.

        Returns:
            Optional[str]: The resolved endpoint or None.
        """
        return get_agent_address(destination)


class RulesBasedResolver(Resolver):
    def __init__(self, rules: Dict[str, str]):
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
            Optional[str]: The resolved endpoint or None.
        """
        return self._rules.get(destination)
