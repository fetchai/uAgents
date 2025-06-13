"""
This module provides methods related to agent bases subscriptions.

Example usage:
```
@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    # verify that the sender has an ongoing subscription with our agent
    if not is_subscription_valid(identity=ctx.agent.identity, requester_address=sender):
        await ctx.send(sender, ErrorMessage(error="Subscription needed for this agent"))
        return

    # process the message
    ...
```

"""

from datetime import datetime
from secrets import token_bytes

import requests

from uagents_core.config import AgentverseConfig
from uagents_core.identity import Identity
from uagents_core.storage import compute_attestation


def is_subscription_valid(
    identity: Identity,
    requester_address: str,
    agentverse_config: AgentverseConfig | None = None,
) -> bool:
    """
    Check if the requester has a valid subscription with the agent.
    This function is used to verify that the sender has an active subscription
    before processing the message.

    Args:
        identity (Identity): The identity of the agent that is requested.
        requester_address (str): The address of the requester to check.
        agentverse_config (AgentverseConfig | None): The configuration for the Agentverse.
            If not provided, defaults to a new instance of AgentverseConfig.

    Returns:
        bool: True if the sender has a valid subscription, False otherwise.
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
    headers = {"Authorization": f"Agent {attestation}"}
    response = requests.get(url=url, headers=headers, timeout=10)

    return response.status_code == 200
