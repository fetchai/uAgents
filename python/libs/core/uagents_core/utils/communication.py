import json
import random
import urllib.parse
from typing import Any, List, Optional, Tuple
from uuid import UUID, uuid4

import requests

from uagents_core.config import (
    AGENT_ADDRESS_LENGTH,
    AGENT_PREFIX,
    DEFAULT_ALMANAC_API_PATH,
    DEFAULT_MAX_ENDPOINTS,
    AgentverseConfig,
)
from uagents_core.crypto import Identity, is_user_address
from uagents_core.envelope import Envelope
from uagents_core.logger import get_logger

logger = get_logger("uagents_core.utils.communication")


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


def parse_identifier(identifier: str) -> Tuple[str, str, str]:
    """
    Parse an agent identifier string into prefix, name, and address.

    Args:
        identifier (str): The identifier string to be parsed.

    Returns:
        Tuple[str, str, str]: A Tuple containing the prefix, name, and address as strings.
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


def lookup_endpoint_for_agent(
    agent_identifier: str,
    *,
    max_endpoints: int = DEFAULT_MAX_ENDPOINTS,
    agentverse_config: Optional[AgentverseConfig] = None,
) -> List[str]:
    """
    Look up the endpoints for an agent using the Almanac API.

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
    logger.debug("looking up endpoint for agent", extra=request_meta)
    r = requests.get(f"{almanac_api}/agents/{agent_address}")
    r.raise_for_status()

    request_meta["response_status"] = r.status_code
    logger.info(
        "Got response looking up agent endpoint",
        extra=request_meta,
    )

    endpoints = r.json().get("endpoints", [])

    if len(endpoints) > 0:
        endpoints = [val.get("url") for val in endpoints]
        weights = [val.get("weight") for val in endpoints]
        return weighted_random_sample(
            endpoints,
            weights=weights,
            k=min(max_endpoints, len(endpoints)),
        )

    return []


def send_message(
    destination: str,
    message_schema_digest: str,
    message_body: Any,
    sender: Identity,
    *,
    session_id: Optional[UUID] = None,
    protocol_digest: Optional[str] = None,
    agentverse_config: Optional[AgentverseConfig] = None,
):
    """
    Send a message (dict) to an agent.

    Args:
        destination (str): The address of the target agent.
        message_schema_digest (str): The digest of the model that is being used
        message_body (Any): The payload of the message.
        sender (Identity): The identity of the sender.
        session (UUID): The unique identifier for the dialogue between two agents
        protocol_digest (str): The digest of the protocol that is being used
        agentverse_config (AgentverseConfig): The configuration for the agentverse API
    Returns:
        None
    """
    json_payload = json.dumps(message_body, separators=(",", ":"))

    env = Envelope(
        version=1,
        sender=sender.address,
        target=destination,
        session=session_id or uuid4(),
        schema_digest=message_schema_digest,
        protocol_digest=protocol_digest,
    )

    env.encode_payload(json_payload)
    env.sign(sender)

    logger.debug("Sending message to agent", extra={"envelope": env.model_dump()})

    # query the almanac to lookup the destination agent
    agentverse_config = agentverse_config or AgentverseConfig()
    endpoints = lookup_endpoint_for_agent(
        destination, agentverse_config=agentverse_config
    )

    if len(endpoints) == 0:
        logger.error(
            "No endpoints found for agent", extra={"agent_address": destination}
        )
        return

    # send the envelope to the destination agent
    request_meta = {"agent_address": destination, "agent_endpoint": endpoints[0]}
    logger.debug("Sending message to agent", extra=request_meta)
    r = requests.post(
        endpoints[0],
        headers={"content-type": "application/json"},
        data=env.model_dump_json(),
    )
    r.raise_for_status()
    logger.info("Sent message to agent", extra=request_meta)
