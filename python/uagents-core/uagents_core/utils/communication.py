import json
import urllib.parse
from typing import Any
from uuid import UUID, uuid4

import requests

from uagents_core.communication import parse_identifier, weighted_random_sample
from uagents_core.config import (
    DEFAULT_ALMANAC_API_PATH,
    DEFAULT_MAX_ENDPOINTS,
    AgentverseConfig,
)
from uagents_core.crypto import Identity
from uagents_core.envelope import Envelope
from uagents_core.logger import get_logger

logger = get_logger("uagents_core.utils.communication")


def lookup_endpoint_for_agent(
    agent_identifier: str,
    *,
    max_endpoints: int = DEFAULT_MAX_ENDPOINTS,
    agentverse_config: AgentverseConfig | None = None,
) -> list[str]:
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
        urls = [val.get("url") for val in endpoints]
        weights = [val.get("weight") for val in endpoints]
        return weighted_random_sample(
            urls,
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
    session_id: UUID | None = None,
    protocol_digest: str | None = None,
    agentverse_config: AgentverseConfig | None = None,
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
        timeout=5,
    )
    r.raise_for_status()
    logger.info("Sent message to agent", extra=request_meta)
