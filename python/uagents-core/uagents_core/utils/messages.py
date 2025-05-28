"""
This module provides methods to enable an identity to interact with other agents.
"""

import json
from typing import Any, Literal
from uuid import UUID, uuid4

import requests

from uagents_core.config import DEFAULT_REQUEST_TIMEOUT, AgentverseConfig
from uagents_core.envelope import Envelope
from uagents_core.helpers import weighted_random_sample
from uagents_core.identity import Identity
from uagents_core.logger import get_logger
from uagents_core.models import Model
from uagents_core.types import DeliveryStatus, MsgStatus
from uagents_core.utils.resolver import lookup_endpoint_for_agent

logger = get_logger("uagents_core.utils.messages")


def generate_message_envelope(
    destination: str,
    message_schema_digest: str,
    message_body: Any,
    sender: Identity,
    *,
    session_id: UUID | None = None,
    protocol_digest: str | None = None,
) -> Envelope:
    """
    Generate an envelope for a message to be sent to an agent.

    Args:
        destination (str): The address of the target agent.
        message_schema_digest (str): The digest of the model that is being used
        message_body (Any): The payload of the message.
        sender (Identity): The identity of the sender.
        session (UUID): The unique identifier for the dialogue between two agents
        protocol_digest (str): The digest of the protocol that is being used
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

    return env


def send_message(
    endpoint: str, envelope: Envelope, timeout: int = DEFAULT_REQUEST_TIMEOUT
) -> requests.Response:
    """
    A helper function to send a message to an agent.

    Args:
        endpoint (str): The endpoint to send the message to.
        envelope (Envelope): The envelope containing the message.
        timeout (int, optional): Requests timeout. Defaults to DEFAULT_REQUEST_TIMEOUT.

    Returns:
        requests.Response: Response object from the request.
    """
    response = requests.post(
        url=endpoint,
        headers={"content-type": "application/json"},
        data=envelope.model_dump_json(),
        timeout=timeout,
    )
    response.raise_for_status()
    return response


def send_message_to_agent(
    destination: str,
    msg: Model,
    sender: Identity,
    *,
    session_id: UUID | None = None,
    strategy: Literal["first", "random", "all"] = "first",
    agentverse_config: AgentverseConfig | None = None,
) -> list[MsgStatus]:
    """
    Send a message to an agent with default settings.

    Args:
        destination (str): The address of the target agent.
        msg (Model): The message to be sent.
        sender (Identity): The identity of the sender.
        session_id (UUID, optional): The unique identifier for the dialogue between two agents.
        strategy (Literal["first", "random", "all"], optional): The strategy to use when
            selecting an endpoint.
        agentverse_config (AgentverseConfig, optional): The configuration for the agentverse.
    """
    agentverse_config = agentverse_config or AgentverseConfig()
    endpoints = lookup_endpoint_for_agent(
        agent_identifier=destination, agentverse_config=agentverse_config
    )
    if not endpoints:
        logger.error("No endpoints found for agent", extra={"destination": destination})
        return []

    env = generate_message_envelope(
        destination=destination,
        message_schema_digest=Model.build_schema_digest(msg),
        message_body=json.loads(msg.model_dump_json()),
        sender=sender,
        session_id=session_id,
    )
    match strategy:
        case "first":
            endpoints = endpoints[:1]
        case "random":
            endpoints = weighted_random_sample(endpoints)

    endpoints: list[str] = endpoints if strategy == "all" else endpoints[:1]

    result: list[MsgStatus] = []
    for endpoint in endpoints:
        try:
            response = send_message(endpoint, env)
            logger.info("Sent message to agent", extra={"agent_endpoint": endpoint})
            result.append(
                MsgStatus(
                    status=DeliveryStatus.SENT,
                    detail=response.text,
                    destination=destination,
                    endpoint=endpoint,
                    session=env.session,
                )
            )
        except requests.RequestException as e:
            logger.error("Failed to send message to agent", extra={"error": str(e)})
            result.append(
                MsgStatus(
                    status=DeliveryStatus.FAILED,
                    detail=str(e),
                    destination=destination,
                    endpoint=endpoint,
                    session=env.session,
                )
            )
    return result
