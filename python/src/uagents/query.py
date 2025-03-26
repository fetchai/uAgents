"""Query Envelopes."""

from typing_extensions import deprecated
from uagents_core.envelope import Envelope
from uagents_core.identity import generate_user_address
from uagents_core.models import Model
from uagents_core.types import MsgStatus

from uagents.communication import send_sync_message
from uagents.resolver import Resolver


@deprecated(
    "Query is deprecated and will be removed in a future release, use send_sync_message instead."
)
async def query(
    destination: str,
    message: Model,
    resolver: Resolver | None = None,
    timeout: int = 30,
) -> MsgStatus | Envelope:
    """
    Query a remote agent with a message and retrieve the response envelope.

    Args:
        destination (str): The destination address of the remote agent.
        message (Model): The message to send.
        resolver (Resolver | None): The resolver to use for endpoint resolution.
        Defaults to GlobalResolver.
        timeout (int): The timeout for the query in seconds. Defaults to 30.

    Returns:
        MsgStatus | Envelope: The response envelope if successful, otherwise MsgStatus.
    """
    response = await send_sync_message(
        destination=destination,
        message=message,
        response_type=None,
        sender=generate_user_address(),
        resolver=resolver,
        timeout=timeout,
    )
    if isinstance(response, (MsgStatus, Envelope)):
        return response
    raise ValueError("Invalid response received.")
