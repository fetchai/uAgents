"""
This module provides helpers for executing Agentverse tool integrations
(Pipedream-backed actions such as Slack, Google Calendar or GitHub) on behalf
of an agent.

The Agentverse Tools API resolves the calling agent to its owner account and
runs the action using the owner's connected integration. The agent never holds
provider credentials; it authenticates with a short-lived agent attestation.

Example usage:
```
from uagents_core.utils.integrations import execute_tool, sync_execute_tool

# inside an asynchronous uAgent handler
result = await execute_tool(
    identity=ctx.agent.identity,
    tool_name="slack-post-message",
    params={"channel": "#general", "text": "hello"},
)

# synchronous
result = sync_execute_tool(
    identity=agent_identity,
    tool_name="slack-post-message",
    params={"channel": "#general", "text": "hello"},
)
```
"""

import os
from datetime import datetime, timezone
from secrets import token_bytes

import httpx
import requests

from uagents_core.config import AgentverseConfig
from uagents_core.identity import Identity
from uagents_core.logger import get_logger
from uagents_core.storage import compute_attestation

logger = get_logger("uagents_core.utils.integrations")

TOOLS_BASE_URL_ENV_VAR = "TOOLS_BASE_URL"
TOOLS_EXECUTE_PATH = "/v2/tools/execute"
DEFAULT_TOOL_EXECUTION_TIMEOUT = 20
ATTESTATION_VALIDITY_SECS = 60


class ToolExecutionError(RuntimeError):
    """Raised when a tool execution fails or is refused by Agentverse."""

    def __init__(
        self,
        message: str,
        *,
        tool_name: str,
        status_code: int | None = None,
        detail: str | None = None,
    ):
        super().__init__(message)
        self.tool_name = tool_name
        self.status_code = status_code
        self.detail = detail


def _resolve_base_url(base_url: str | None) -> str:
    """Resolve the Tools API origin: explicit arg, then ``TOOLS_BASE_URL``, then Agentverse."""
    if base_url:
        return base_url.rstrip("/")
    env_url = os.environ.get(TOOLS_BASE_URL_ENV_VAR)
    if env_url:
        return env_url.rstrip("/")
    return AgentverseConfig().url


def _auth_header(identity: Identity) -> dict[str, str]:
    """Build the ``Authorization: Agent <attestation>`` header for a request."""
    attestation = compute_attestation(
        identity=identity,
        validity_start=datetime.now(timezone.utc),
        validity_secs=ATTESTATION_VALIDITY_SECS,
        nonce=token_bytes(32),
    )
    return {"Authorization": f"Agent {attestation}"}


def _raise_for_tool_error(tool_name: str, status_code: int, detail: str) -> None:
    """Raise a :class:`ToolExecutionError` with a user-readable message."""
    if status_code == 400:
        raise ToolExecutionError(
            f"Unsupported tool '{tool_name}'.",
            tool_name=tool_name,
            status_code=status_code,
            detail=detail,
        )
    if status_code == 403:
        # Either the agent has no registered owner, or the owner has not allowed this tool.
        raise ToolExecutionError(
            f"Agentverse refused to run {tool_name}: {detail}",
            tool_name=tool_name,
            status_code=status_code,
            detail=detail,
        )
    if status_code == 404:
        raise ToolExecutionError(
            f"{tool_name} is not connected. The owner must connect it on the "
            "Agent Integrations page.",
            tool_name=tool_name,
            status_code=status_code,
            detail=detail,
        )
    if status_code == 502:
        raise ToolExecutionError(
            f"{tool_name} failed. If the connection was revoked, the owner must "
            "reconnect it on the Agent Integrations page.",
            tool_name=tool_name,
            status_code=status_code,
            detail=detail,
        )
    raise ToolExecutionError(
        f"Could not execute {tool_name} (HTTP {status_code}): {detail}",
        tool_name=tool_name,
        status_code=status_code,
        detail=detail,
    )


async def execute_tool(
    identity: Identity,
    tool_name: str,
    params: dict | None = None,
    *,
    base_url: str | None = None,
    timeout: int = DEFAULT_TOOL_EXECUTION_TIMEOUT,
) -> dict:
    """
    Execute a platform tool asynchronously on behalf of an agent.

    Calls ``POST {base_url}/v2/tools/execute`` on the Agentverse Tools API.
    The API resolves the calling agent to its owner account and performs the
    provider call using the owner's connected integration; the agent never
    holds a provider credential.

    Args:
        identity (Identity): The identity of the calling agent.
        tool_name (str): The Agentverse tool name to execute
            (e.g. 'slack-post-message').
        params (dict, optional): Tool-specific parameters forwarded to the
            underlying API call.
        base_url (str, optional): Origin of the Tools API. Defaults to the
            ``TOOLS_BASE_URL`` environment variable if set, otherwise Agentverse.
        timeout (int, optional): Request timeout in seconds. Defaults to 20.

    Returns:
        dict: The tool execution response (``{"tool": ..., "result": ...}``).

    Raises:
        ToolExecutionError: If the tool could not be executed, with a
            user-readable message.
    """
    url = f"{_resolve_base_url(base_url)}{TOOLS_EXECUTE_PATH}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url=url,
                json={"tool": tool_name, "params": params or {}},
                headers=_auth_header(identity),
            )
    except httpx.HTTPError as error:
        raise ToolExecutionError(
            f"Could not reach Agentverse to run {tool_name}. Please try again.",
            tool_name=tool_name,
        ) from error
    if response.status_code != 200:
        _raise_for_tool_error(tool_name, response.status_code, response.text)
    return response.json()


def sync_execute_tool(
    identity: Identity,
    tool_name: str,
    params: dict | None = None,
    *,
    base_url: str | None = None,
    timeout: int = DEFAULT_TOOL_EXECUTION_TIMEOUT,
) -> dict:
    """
    Execute a platform tool synchronously on behalf of an agent.

    The synchronous counterpart of :func:`execute_tool`, following the
    ``sync_resolve`` / ``resolve`` naming convention.

    Args:
        identity (Identity): The identity of the calling agent.
        tool_name (str): The Agentverse tool name to execute
            (e.g. 'slack-post-message').
        params (dict, optional): Tool-specific parameters forwarded to the
            underlying API call.
        base_url (str, optional): Origin of the Tools API. Defaults to the
            ``TOOLS_BASE_URL`` environment variable if set, otherwise Agentverse.
        timeout (int, optional): Request timeout in seconds. Defaults to 20.

    Returns:
        dict: The tool execution response (``{"tool": ..., "result": ...}``).

    Raises:
        ToolExecutionError: If the tool could not be executed, with a
            user-readable message.
    """
    url = f"{_resolve_base_url(base_url)}{TOOLS_EXECUTE_PATH}"
    try:
        response = requests.post(
            url=url,
            json={"tool": tool_name, "params": params or {}},
            headers=_auth_header(identity),
            timeout=timeout,
        )
    except requests.RequestException as error:
        raise ToolExecutionError(
            f"Could not reach Agentverse to run {tool_name}. Please try again.",
            tool_name=tool_name,
        ) from error
    if response.status_code != 200:
        _raise_for_tool_error(tool_name, response.status_code, response.text)
    return response.json()
