"""Endpoint Resolver."""

import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

import aiohttp
from pydantic import BaseModel
from uagents_core.helpers import weighted_random_sample
from uagents_core.identity import parse_identifier

from uagents.config import (
    ALMANAC_API_URL,
    DEFAULT_MAX_ENDPOINTS,
    MAINNET_PREFIX,
    TESTNET_PREFIX,
)
from uagents.network import (
    get_almanac_contract,
    get_name_service_contract,
)
from uagents.types import AgentNetwork
from uagents.utils import get_logger

LOGGER: logging.Logger = get_logger("resolver", logging.WARNING)


class AgentRecord(BaseModel):
    address: str
    weight: float


class DomainRecord(BaseModel):
    name: str
    agents: list[AgentRecord]


class DomainStatus(Enum):
    Registered = "Registered"
    Pending = "Pending"
    Checking = "Checking"
    Updating = "Updating"
    Deleting = "Deleting"
    Failed = "Failed"


class Domain(BaseModel):
    name: str
    status: DomainStatus
    expiry: datetime | None = None
    assigned_agents: list[AgentRecord]


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


def query_record(agent_address: str, network: AgentNetwork) -> dict:
    """
    Query an agent record from the Almanac contract.

    Args:
        agent_address (str): The address of the agent.
        network (AgentNetwork): The network to query (mainnet or testnet).

    Returns:
        dict: The query result.
    """

    query_msg = {
        "query_record": {"agent_address": agent_address, "record_type": "service"}
    }

    contract = get_almanac_contract(network)
    if not contract:
        raise ValueError(f"Almanac contract not found for {network}.")

    return contract.query(query_msg)


def get_agent_address(name: str, network: AgentNetwork) -> str | None:
    """
    Get the agent address associated with the provided domain from the name service contract.

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


def build_identifier(
    prefix: str | None = None, name: str | None = None, address: str | None = None
) -> str:
    """
    Build an agent identifier string from prefix, name, and address.

    Args:
        prefix (str): The prefix to be used in the identifier.
        name (str): The name to be used in the identifier.
        address (str): The address to be used in the identifier.

    Returns:
        str: The constructed identifier string.
    """

    identifier = ""
    if prefix:
        identifier += f"{prefix}://"
    if name:
        identifier += name + ("/" if address else "")
    if address:
        identifier += address

    return identifier


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
            max_endpoints=self._max_endpoints, almanac_api_url=almanac_api_url
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

        result: dict | None = None
        if prefix == MAINNET_PREFIX:
            result = query_record(agent_address=address, network="mainnet")
        elif prefix == TESTNET_PREFIX:
            result = query_record(agent_address=address, network="testnet")
        elif prefix == "":
            for network in ["mainnet", "testnet"]:
                try:
                    result = query_record(agent_address=address, network="mainnet")
                    if result is not None:
                        break
                except ValueError:
                    if network == "testnet":
                        raise

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
            prefix, _, address = parse_identifier(destination)

            params = {"prefix": prefix} if prefix else None
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    url=f"{self._almanac_api_url}/agents/{address}",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response,
            ):
                if response.status != 200:
                    LOGGER.debug(
                        f"Failed to resolve agent {address} from {self._almanac_api_url}, "
                        "resolving via Almanac contract..."
                    )
                    return None, []

                agent = await response.json()

            expiry_str = agent.get("expiry", None)
            if expiry_str is None:
                return None, []

            endpoint_list = agent.get("endpoints", [])

            if len(endpoint_list) > 0:
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
    def __init__(
        self, max_endpoints: int | None = None, almanac_api_url: str | None = None
    ):
        """
        Initialize the NameServiceResolver.

        Args:
            max_endpoints (int | None): The maximum number of endpoints to return.
        """
        self._max_endpoints = max_endpoints or DEFAULT_MAX_ENDPOINTS
        self._almanac_api_url = almanac_api_url
        self._almanac_api_resolver = AlmanacApiResolver(
            almanac_api_url=almanac_api_url, max_endpoints=self._max_endpoints
        )

    async def _api_resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination using the Almanac Domains API.

        Args:
            destination (str): The agent identifier to resolve.

        Returns:
            Tuple[Optional[str], List[str]]: The address (if available) and resolved endpoints.
        """
        try:
            prefix, domain, _ = parse_identifier(destination)

            params = {"prefix": prefix} if prefix else None
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{self._almanac_api_url}/domains/{domain}",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response,
            ):
                if response.status != 200:
                    LOGGER.debug(
                        f"Failed to resolve name {domain} from {self._almanac_api_url}: "
                        f"{response.status}: {await response.text()}"
                    )
                    return None, []

                domain_record = Domain.model_validate(await response.json())

            agent_records = domain_record.assigned_agents
            if len(agent_records) == 0:
                return None, []
            elif len(agent_records) == 1:
                address = agent_records[0].address
            else:
                addresses = [val.address for val in agent_records]
                weights = [val.weight for val in agent_records]
                address = weighted_random_sample(addresses, weights=weights, k=1)[0]

            identifier = build_identifier(prefix=prefix, address=address)
            return await self._almanac_api_resolver.resolve(identifier)

        except Exception as ex:
            LOGGER.error(f"Error when resolving {destination}: {ex}")
            return None, []

    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination using the NameService contract.

        Args:
            destination (str): The destination name to resolve.

        Returns:
            tuple[str | None, list[str]]: The address (if available) and resolved endpoints.
        """
        prefix, name, _ = parse_identifier(destination)

        api_result = await self._api_resolve(destination)

        if api_result:
            return api_result

        address: str | None = None
        if prefix == MAINNET_PREFIX:
            address = get_agent_address(name, "mainnet")
        elif prefix == TESTNET_PREFIX:
            address = get_agent_address(name, "testnet")
        elif prefix == "":
            for network in ["mainnet", "testnet"]:
                address = get_agent_address(name, network)  # type: ignore
                if address is not None:
                    break
        else:
            raise ValueError(f"Invalid prefix: {prefix}")

        if address is not None:
            identifier = build_identifier(prefix=prefix, address=address)
            return await self._almanac_api_resolver.resolve(identifier)

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
