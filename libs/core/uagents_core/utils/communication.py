import json
from typing import Optional, Any
from uuid import uuid4, UUID

import requests
import urllib.parse

from uagents_core.crypto import Identity
from uagents_core.envelope import Envelope
from uagents_core.config import DEFAULT_ALMANAC_API_PATH, AgentverseConfig
from uagents_core.logger import get_logger



logger = get_logger("uagents_core.utils.communication")


def lookup_endpoint_for_agent(
    agent_address: str,
    *,
    agentverse_config: AgentverseConfig = AgentverseConfig(),
) -> str:
    almanac_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_ALMANAC_API_PATH)

    request_meta = {
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

    return r.json()["endpoints"][0]["url"]


def send_message_dict(
    destination: str,
    message_schema_digest: str,
    message_body: Any,
    sender: Identity,
    *,
    session_id: UUID = uuid4(),
    protocol_digest: Optional[str] = None,
    agentverse_config: AgentverseConfig = AgentverseConfig(),
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
        session=session_id,
        schema_digest=message_schema_digest,
        protocol_digest=protocol_digest,
    )

    env.encode_payload(json_payload)
    env.sign(sender)

    logger.debug("Sending message to agent", extra={"envelope": env.model_dump()})

    # query the almanac to lookup the destination agent
    endpoint = lookup_endpoint_for_agent(destination, agentverse_config=agentverse_config)

    # send the envelope to the destination agent
    request_meta = {"agent_address": destination, "agent_endpoint": endpoint}
    logger.debug("Sending message to agent", extra=request_meta)
    r = requests.post(
        endpoint,
        headers={"content-type": "application/json"},
        data=env.model_dump_json(),
    )
    r.raise_for_status()
    logger.info("Sent message to agent", extra=request_meta)
