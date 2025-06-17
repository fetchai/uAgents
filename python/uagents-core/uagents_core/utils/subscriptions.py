"""
This module provides methods related to agent bases subscriptions.

Example usage:
```
from uagents_core.contrib.protocols.subscriptions import TierType

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    subscription_tier = get_subscription_tier(
        identity=ctx.agent.identity,
        requester_address=sender
    )

    if subscription_tier == TierType.PLUS:
        ...

    if subscription_tier == TierType.PRO:
        ...

    ...
```

"""

from datetime import datetime
from secrets import token_bytes

import requests

from uagents_core.config import AgentverseConfig
from uagents_core.contrib.protocols.subscriptions import TierType
from uagents_core.identity import Identity
from uagents_core.logger import get_logger
from uagents_core.storage import compute_attestation

logger = get_logger("uagents_core.utils.subscriptions")


def get_subscription_tier(
    identity: Identity,
    requester_address: str,
    agentverse_config: AgentverseConfig | None = None,
) -> TierType:
    """
    Get the subscription tier of the requester for a specific agent.

    This function is used to verify the type of subscription before processing
    an incoming message.

    Args:
        identity (Identity): The identity of the agent that is requested.
        requester_address (str): The address of the requester to check.
        agentverse_config (AgentverseConfig | None): The configuration for the Agentverse.
            If not provided, defaults to a new instance of AgentverseConfig.

    Returns:
        TierType: The subscription tier type of the requester.
    """
    if not agentverse_config:
        agentverse_config = AgentverseConfig()
    attestation: str = compute_attestation(
        identity=identity,
        validity_start=datetime.now(),
        validity_secs=60,
        nonce=token_bytes(nbytes=32),
    )
    url: str = (
        f"{agentverse_config.payments_endpoint}/subscriptions"
        + f"/{identity.address}/{requester_address}"
    )
    headers: dict[str, str] = {"Authorization": f"Agent {attestation}"}

    try:
        response = requests.get(url=url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to get subscription tier: {e}")
        return TierType.FREE

    data: dict = response.json()
    return data.get("tier_type", TierType.FREE)
