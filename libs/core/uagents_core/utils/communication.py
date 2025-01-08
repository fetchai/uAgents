import json
from typing import Optional, Any
from uuid import uuid4, UUID

import requests
import urllib.parse

from uagents_core.crypto import Identity
from uagents_core.envelope import Envelope
from uagents_core.config import DEFAULT_AGENTVERSE_URL, DEFAULT_ALMANAC_API_PATH
from uagents_core.logger import get_logger



logger = get_logger("uagents_core.utils.communication")


def lookup_endpoint_for_agent(agent_address: str, *, agentverse_url: Optional[str] = None) -> str:
    agentverse_url = agentverse_url or DEFAULT_AGENTVERSE_URL
    almanac_api = urllib.parse.urljoin(agentverse_url, DEFAULT_ALMANAC_API_PATH)

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
    sender: Identity,
    destination: str,
    payload: Any,
    protocol_digest: str,
    model_digest: str,
    session: UUID = uuid4(),
    *,
    agentverse_url: Optional[str] = None,
):
    """
    Send a message (dict) to an agent.

    Args:
        sender (Identity): The identity of the sender.
        destination (str): The address of the target agent.
        payload (Any): The payload of the message.
        protocol_digest (str): The digest of the protocol that is being used
        model_digest (str): The digest of the model that is being used
        session (UUID): The unique identifier for the dialogue between two agents
        agentverse_url (Optional[str]): The URL of the agentverse API
    
    Returns:
        None
    """
    json_payload = json.dumps(payload, separators=(",", ":"))

    env = Envelope(
        version=1,
        sender=sender.address,
        target=destination,
        session=session,
        schema_digest=model_digest,
        protocol_digest=protocol_digest,
    )

    env.encode_payload(json_payload)
    env.sign(sender)

    logger.debug("Sending message to agent", extra={"envelope": env.model_dump()})

    # query the almanac to lookup the destination agent
    endpoint = lookup_endpoint_for_agent(destination, agentverse_url=agentverse_url)

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
