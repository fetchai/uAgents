import logging
from datetime import datetime, timezone
from secrets import token_bytes

from uagents_core.adapters.common.config import (
    AGENT_AUTH_TOKEN_VALIDITY,
    DEFAULT_HTTP_REQUESTS_TIMEOUT,
)
from uagents_core.config import AgentverseConfig
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity, is_user_address
from uagents_core.registration import RegistrationRequest
from uagents_core.storage import compute_attestation
from uagents_core.utils.registration import (
    AgentverseRequestError,
    _send_post_request_agentverse,
)

for ch in ["uagents_core.utils.resolver", "uagents_core.utils.messages"]:
    logging.getLogger(ch).setLevel(logging.ERROR)


def generate_agent_auth_token(id: Identity) -> str:
    return compute_attestation(
        id, datetime.now(timezone.utc), AGENT_AUTH_TOKEN_VALIDITY, token_bytes(32)
    )


def _register_to_agentverse(
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
