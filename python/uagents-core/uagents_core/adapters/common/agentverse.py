import json
import logging
from datetime import datetime, timezone
from secrets import token_bytes
from uuid import UUID

import httpx

from pydantic import BaseModel
from uagents_core.adapters.common.config import (
    AGENT_AUTH_TOKEN_VALIDITY,
    DEFAULT_HTTP_REQUESTS_TIMEOUT,
)
from uagents_core.config import AgentverseConfig
from uagents_core.contrib.protocols.chat import chat_protocol_spec
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.models import Model
from uagents_core.types import JsonStr
from uagents_core.identity import Identity, is_user_address
from uagents_core.protocol import ProtocolSpecification
from uagents_core.registration import RegistrationRequest, AgentStatusUpdate
from uagents_core.storage import compute_attestation
from uagents_core.utils.messages import generate_message_envelope, parse_envelope_raw
from uagents_core.utils.registration import (
    AgentverseRequestError,
    _send_post_request_agentverse,
)
from uagents_core.utils.resolver import AlmanacResolver


CHAT_PROTOCOL = ProtocolSpecification.compute_digest(chat_protocol_spec.manifest())


for ch in ["uagents_core.utils.resolver", "uagents_core.utils.messages", "httpx"]:
    logging.getLogger(ch).setLevel(logging.ERROR)


def generate_agent_auth_token(id: Identity) -> str:
    return compute_attestation(
        id, datetime.now(timezone.utc), AGENT_AUTH_TOKEN_VALIDITY, token_bytes(32)
    )


def register_to_agentverse_sync(
    request: RegistrationRequest,
    headers: dict[str, str],
    agentverse: AgentverseConfig,
    timeout: int = DEFAULT_HTTP_REQUESTS_TIMEOUT,
):
    try:
        _send_post_request_agentverse(
            url=agentverse.agents_api,
            data=request,
            headers=headers,
            timeout=timeout,
        )
    except AgentverseRequestError as e:
        raise
    except Exception as e:
        raise


def verify_envelope(envelope: Envelope) -> bool:
    try:
        if is_user_address(envelope.sender):
            return True
        return envelope.verify()
    except Exception:
        return False


async def set_agent_status(
    agent: Identity,
    active: bool,
    agentverse: AgentverseConfig,
    timeout: int = DEFAULT_HTTP_REQUESTS_TIMEOUT,
):
    update = AgentStatusUpdate(agent_identifier=agent.address, is_active=active)
    update.sign(agent)

    await _post_data(
        url=f"{agentverse.almanac_api}/agents/{agent.address}/status",
        data=update,
        timeout=timeout,
    )


async def _post_data(
    url: str,
    data: BaseModel,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_HTTP_REQUESTS_TIMEOUT,
) -> httpx.Response:
    headers = headers or dict()
    headers["Content-Type"] = "application/json"

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url=url,
            data=data.model_dump_json(),
            headers=headers,
        )
        response.raise_for_status()

        return response


async def send_message_to_agent(
    destination: str,
    msg: Model,
    sender: Identity,
    *,
    session_id: UUID | None = None,
    agentverse_config: AgentverseConfig,
    sync: bool = False,
    timeout: int = DEFAULT_HTTP_REQUESTS_TIMEOUT,
    response_type: type[Model] | set[type[Model]] | None = None,
) -> Model | JsonStr | None:
    resolver = AlmanacResolver(agentverse_config=agentverse_config)
    _, endpoints = await resolver.resolve(destination)
    if len(endpoints) == 0:
        raise RuntimeError(f"Couldn't resolve endpoint for agent {destination}")

    env = generate_message_envelope(
        destination=destination,
        message_schema_digest=Model.build_schema_digest(msg),
        message_body=json.loads(msg.model_dump_json()),
        sender=sender,
        session_id=session_id,
    )

    headers = None
    if sync:
        headers = {"x-uagents-connection": "sync"}

    response = await _post_data(
        url=endpoints[0],
        data=env,
        headers=headers,
        timeout=timeout,
    )

    if response.is_success and sync:
        return parse_envelope_raw(response.text, response_type)

    return None
