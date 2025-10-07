"""
This module provides methods to enable an identity to interact with other agents.
"""

import contextlib
import json
from typing import Any, Literal
from uuid import UUID, uuid4

import requests
from pydantic import ValidationError

from uagents_core.config import (
    DEFAULT_MAX_ENDPOINTS,
    DEFAULT_REQUEST_TIMEOUT,
    AgentverseConfig,
)
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.logger import get_logger
from uagents_core.models import Model
from uagents_core.types import DeliveryStatus, JsonStr, MsgStatus, Resolver
from uagents_core.utils.resolver import AlmanacResolver

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
    endpoint: str,
    envelope: Envelope,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
    sync: bool = False,
) -> requests.Response:
    """
    A helper function to send a message to an agent.

    Args:
        endpoint (str): The endpoint to send the message to.
        envelope (Envelope): The envelope containing the message.
        timeout (int, optional): Requests timeout. Defaults to DEFAULT_REQUEST_TIMEOUT.
        sync (bool, optional): Whether to send the message synchronously. Defaults to False.

    Returns:
        requests.Response: Response object from the request.
    """
    headers = {"content-type": "application/json"}
    if sync:
        headers["x-uagents-connection"] = "sync"
    response = requests.post(
        url=endpoint,
        headers=headers,
        data=envelope.model_dump_json(),
        timeout=timeout,
    )
    response.raise_for_status()
    return response


def parse_envelope(
    env: Envelope,
    message_type: type[Model] | set[type[Model]] | None = None,
) -> Model | str:
    """
    Parse the response from a synchronous message.

    Args:
        env (Envelope): The envelope.
        message_type (type[Model] | set[type[Model]] | None, optional):
            The expected type of the message contained in the envelope.
            If None, the raw JSON string will be returned. Defaults to None.
    Returns:
        Model | str: The parsed message model or JSON string.
    """
    message_json = env.decode_payload()

    msg: Model | None = None
    if message_type:
        response_types = (
            {message_type} if isinstance(message_type, type) else message_type
        )

        for r_type in response_types:
            with contextlib.suppress(ValidationError):
                msg = r_type.parse_raw(message_json)

    return msg or message_json


def parse_envelope_raw(
    env_json: str,
    message_type: type[Model] | set[type[Model]] | None = None,
) -> Model | str:
    """
    Parse an envelope in JSON str format

    Args:
        env_json (str): The JSON string of the response envelope.
        message_type (type[Model] | set[type[Model]] | None, optional):
            The expected type of the message contained in the envelope.
    Returns:
        Model | str: The parsed message model or JSON string.
    """
    env = Envelope.model_validate_json(env_json)
    return parse_envelope(env, message_type)


def send_message_to_agent(
    destination: str,
    msg: Model,
    sender: Identity,
    *,
    session_id: UUID | None = None,
    strategy: Literal["first", "random", "all"] = "first",
    agentverse_config: AgentverseConfig | None = None,
    resolver: Resolver | None = None,
    sync: bool = False,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
    response_type: type[Model] | set[type[Model]] | None = None,
) -> list[MsgStatus] | Model | JsonStr:
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
        resolver (Resolver, optional): The resolver to use for finding endpoints.
        sync (bool, optional): Whether to send the message synchronously and wait for a response.
        response_type (type[Model] | set[type[Model]] | None, optional):
            The expected response type(s) for a sync message.

    Returns:
        list[MsgStatus] | Model | JsonStr: A list of message statuses
            or the response model or json string if sync is True.
    """
    agentverse_config = agentverse_config or AgentverseConfig()

    if not resolver:
        max_endpoints = 1 if strategy in ["first", "random"] else DEFAULT_MAX_ENDPOINTS
        resolver = AlmanacResolver(
            max_endpoints=max_endpoints,
            agentverse_config=agentverse_config,
        )
    endpoints = resolver.sync_resolve(destination)
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

    status_result: list[MsgStatus] = []
    response: requests.Response | None = None
    for endpoint in endpoints:
        try:
            response = send_message(endpoint, env, timeout=timeout, sync=sync)
            status_result.append(
                MsgStatus(
                    status=DeliveryStatus.SENT,
                    detail="Message sent successfully",
                    destination=destination,
                    endpoint=endpoint,
                    session=session_id,
                )
            )
            logger.info("Sent message to agent", extra={"agent_endpoint": endpoint})
            break
        except requests.RequestException as e:
            logger.error("Failed to send message to agent", extra={"error": str(e)})
            status_result.append(
                MsgStatus(
                    status=DeliveryStatus.FAILED,
                    detail=str(e),
                    destination=destination,
                    endpoint=endpoint,
                    session=env.session,
                )
            )

    if response and sync:
        try:
            return parse_envelope_raw(response.text, response_type)
        except ValidationError as e:
            logger.error(
                "Received invalid response envelope",
                extra={"error": str(e), "response": response.text},
            )

    return status_result
