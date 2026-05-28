"""
Async helper for uploading content to Agentverse External Storage.

API reference: agentverse-core services/storage/src/api/routes/public/assets.py
- POST /v1/storage/assets/ accepts Agent attestation auth (get_client dep)
- Request body: NewAsset {contents (base64), mime_type, lifetime_hours (1-24)}
- Response: 201 with Asset {asset_id (UUID)}; 403 if agent not delegated
"""

import base64
import traceback

import httpx

from uagents_core.agentverse.sdk.common.av import generate_agent_auth_token
from uagents_core.agentverse.sdk.common.events import dispatch_event_safe
from uagents_core.agentverse.sdk.common.logger import logger
from uagents_core.agentverse.sdk.common.types import AgentBatchEvents, AgentUri


async def upload_to_storage(
    content: bytes,
    mime_type: str,
    agent_uri: AgentUri,
) -> str:
    """Upload content to Agentverse storage, return an agent-storage:// URI."""
    url = f"{agent_uri.agentverse.storage_api}/assets/"
    headers = {
        "Authorization": f"Agent {generate_agent_auth_token(agent_uri.identity)}",
        "Content-Type": "application/json",
    }
    payload = {
        "contents": base64.b64encode(content).decode(),
        "mime_type": mime_type,
        "lifetime_hours": 24,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 201:
        raise RuntimeError(f"Storage upload failed: {response.status_code}")

    asset_id = response.json()["asset_id"]

    uri = f"agent-storage://{agent_uri.agentverse.base_url}/{asset_id}"
    logger.debug(f"Uploaded to {uri}")
    return uri



async def upload_to_storage_safe(
    content: bytes,
    mime_type: str,
    agent_uri: AgentUri,
) -> str | None:
    """Upload to storage, returning None on failure.

    Logs the error and dispatches a system event so the Agentverse team
    can detect storage service issues without user intervention.
    """
    try:
        return await upload_to_storage(content, mime_type, agent_uri)
    except Exception as e:
        logger.error("Storage upload failed: %s", e)
        await dispatch_event_safe(
            agent_uri,
            AgentBatchEvents.from_exception(e, traceback.format_exc(), "system"),
        )
        return None
