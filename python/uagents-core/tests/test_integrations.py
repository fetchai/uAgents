"""Tool integration helpers: base URL resolution, auth, and error mapping."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
import requests

from uagents_core.identity import Identity
from uagents_core.utils.integrations import (
    ToolExecutionError,
    execute_tool,
    sync_execute_tool,
)

TOOL_NAME = "slack-post-message"
PARAMS = {"channel": "#general", "text": "hello"}
RESULT = {"ok": True, "ts": "1234.5678"}

# Captured at import time, before any monkeypatching, so repeated patches
# within a test always wrap the real client.
REAL_ASYNC_CLIENT = httpx.AsyncClient


@pytest.fixture
def identity() -> Identity:
    return Identity.from_seed("tool-integration-test-seed", 0)


def _fake_response(status_code: int, json_data: dict | None = None):
    response = MagicMock()
    response.status_code = status_code
    response.text = f"HTTP {status_code}"
    if json_data is not None:
        response.json.return_value = json_data
    return response


def _patched_execute_tool(monkeypatch, status_code: int, json_data: dict | None = None):
    post = MagicMock(return_value=_fake_response(status_code, json_data))
    monkeypatch.setattr(
        "uagents_core.utils.integrations.requests.post",
        post,
    )
    return post


class TestSyncExecuteTool:
    def test_success_returns_response(self, monkeypatch, identity):
        _patched_execute_tool(monkeypatch, 200, {"tool": TOOL_NAME, "result": RESULT})

        result = sync_execute_tool(identity, TOOL_NAME, PARAMS)

        assert result == {"tool": TOOL_NAME, "result": RESULT}

    def test_request_payload_and_auth_header(self, monkeypatch, identity):
        post = _patched_execute_tool(
            monkeypatch, 200, {"tool": TOOL_NAME, "result": RESULT}
        )

        sync_execute_tool(identity, TOOL_NAME, PARAMS, base_url="https://hub.example")

        kwargs = post.call_args.kwargs
        assert kwargs["url"] == "https://hub.example/v2/tools/execute"
        assert kwargs["json"] == {"tool": TOOL_NAME, "params": PARAMS}
        assert kwargs["headers"]["Authorization"].startswith("Agent attr:")

    def test_base_url_from_env_var(self, monkeypatch, identity):
        post = _patched_execute_tool(
            monkeypatch, 200, {"tool": TOOL_NAME, "result": RESULT}
        )
        monkeypatch.setenv("TOOLS_BASE_URL", "https://env.example/")

        sync_execute_tool(identity, TOOL_NAME)

        assert post.call_args.kwargs["url"] == "https://env.example/v2/tools/execute"

    def test_explicit_base_url_overrides_env_var(self, monkeypatch, identity):
        post = _patched_execute_tool(
            monkeypatch, 200, {"tool": TOOL_NAME, "result": RESULT}
        )
        monkeypatch.setenv("TOOLS_BASE_URL", "https://env.example")

        sync_execute_tool(identity, TOOL_NAME, base_url="https://explicit.example")

        assert (
            post.call_args.kwargs["url"] == "https://explicit.example/v2/tools/execute"
        )

    def test_error_mapping(self, monkeypatch, identity):
        cases = {
            400: "Unsupported tool",
            403: "refused to run",
            404: "is not connected",
            502: "failed. If the connection was revoked",
            500: "Could not execute",
        }
        for status_code, message_part in cases.items():
            with (
                patch(
                    "uagents_core.utils.integrations.requests.post",
                    return_value=_fake_response(status_code),
                ),
                pytest.raises(ToolExecutionError, match=message_part),
            ):
                sync_execute_tool(identity, TOOL_NAME)

    def test_error_attributes(self, monkeypatch, identity):
        _patched_execute_tool(monkeypatch, 404)

        with pytest.raises(ToolExecutionError) as exc_info:
            sync_execute_tool(identity, TOOL_NAME)

        assert exc_info.value.tool_name == TOOL_NAME
        assert exc_info.value.status_code == 404
        assert isinstance(exc_info.value, RuntimeError)

    def test_connection_error(self, monkeypatch, identity):
        monkeypatch.setattr(
            "uagents_core.utils.integrations.requests.post",
            MagicMock(side_effect=requests.ConnectionError("boom")),
        )

        with pytest.raises(ToolExecutionError, match="Could not reach Agentverse"):
            sync_execute_tool(identity, TOOL_NAME)


class TestExecuteTool:
    def _patch_client(self, monkeypatch, status_code: int, json_data: dict | None):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code, json=json_data)

        def client_factory(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return REAL_ASYNC_CLIENT(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", client_factory)

    @pytest.mark.asyncio
    async def test_success_returns_response(self, monkeypatch, identity):
        self._patch_client(monkeypatch, 200, {"tool": TOOL_NAME, "result": RESULT})

        result = await execute_tool(identity, TOOL_NAME, PARAMS)

        assert result == {"tool": TOOL_NAME, "result": RESULT}

    @pytest.mark.asyncio
    async def test_error_mapping(self, monkeypatch, identity):
        for status_code, message_part in {
            400: "Unsupported tool",
            403: "refused to run",
            404: "is not connected",
            502: "failed. If the connection was revoked",
            500: "Could not execute",
        }.items():
            self._patch_client(monkeypatch, status_code, None)

            with pytest.raises(ToolExecutionError, match=message_part):
                await execute_tool(identity, TOOL_NAME)

    @pytest.mark.asyncio
    async def test_connection_error(self, monkeypatch, identity):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("boom")

        def client_factory(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return REAL_ASYNC_CLIENT(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", client_factory)

        with pytest.raises(ToolExecutionError, match="Could not reach Agentverse"):
            await execute_tool(identity, TOOL_NAME)
