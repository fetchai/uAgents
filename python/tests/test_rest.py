# pylint: disable=protected-access
from unittest.mock import AsyncMock, call, patch

import pytest

from uagents import Agent, Bureau, Context, Model

pytestmark = pytest.mark.asyncio


class Request(Model):
    text: str


class Response(Model):
    text: str


agent = Agent(name="alice")
bob = Agent(name="bob")
bureau = Bureau()


@pytest.mark.order(1)
async def test_rest_get_success():
    @agent.on_rest_get("/get-success", None, Response)
    async def _(_ctx: Context):
        return Response(text="Hi there!")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-success",
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"text": "Hi there!"}',
                }
            ),
        ]
    )


@pytest.mark.order(2)
async def test_rest_post_success():
    @agent.on_rest_post("/post-success", Request, Response)
    async def _(_ctx: Context, req: Request):
        return Response(text=f"Received: {req.text}")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b'{"text": "Hello"}'
        await agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/post-success",
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"text": "Received: Hello"}',
                }
            ),
        ]
    )


@pytest.mark.order(3)
async def test_rest_post_fail_no_body():
    @agent.on_rest_post("/post-body", Request, Response)
    async def _(_ctx: Context, req: Request):
        return Response(text=f"Received: {req.text}")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/post-body",
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "No request body found"}',
                }
            ),
        ]
    )


@pytest.mark.order(4)
async def test_rest_post_fail_invalid_body():
    @agent.on_rest_post("/post-body-inv", Request, Response)
    async def _(_ctx: Context, req: Request):
        return Response(text=f"Received: {req.text}")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b'{"invalid": "body"}'
        await agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/post-body-inv",
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"loc": ["text"], "msg": "field required", "type": "value_error.missing"}',  # noqa: E501
                }
            ),
        ]
    )


@pytest.mark.order(5)
async def test_rest_post_fail_invalid_response():
    wrong_response = {"obviously_wrong": "Oh no!"}
    wrong_response_model = Request(text="Hello")

    @agent.on_rest_post("/post-body-wrong", Request, Response)
    async def _(_ctx: Context, _req: Request):
        return wrong_response

    @agent.on_rest_get("/get-body-wrong", None, Response)
    async def _(_ctx: Context):
        return wrong_response_model

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b'{"text": "Hello"}'
        await agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/post-body-wrong",
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "Handler response does not match response schema."}',
                }
            ),
        ]
    )

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b'{"text": "Hello"}'
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-body-wrong",
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "Handler response does not match response schema."}',
                }
            ),
        ]
    )


@pytest.mark.order(6)
async def test_inspector_rest_wrong_client():
    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/agent_info",
                "client": ("agentverse.ai",),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call({"type": "http.response.body", "body": b'{"error": "forbidden"}'}),
        ]
    )


@pytest.mark.order(7)
async def test_rest_bureau():
    # bureau has one agent and it should route to the agent without additional headers
    @agent.on_rest_get("/get-bureau", None, Response)
    async def _(_ctx: Context):
        return Response(text="agent response")

    bureau.add(agent)

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await bureau._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-bureau",
                "client": ("127.0.0.1",),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"text": "agent response"}',
                }
            ),
        ]
    )

    # bureau adds second agent with same endpoint, should return 400
    @bob.on_rest_get("/get-bureau", None, Response)
    async def _(_ctx: Context):
        return Response(text="bob response")

    bureau.add(bob)

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await bureau._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-bureau",
                "client": ("127.0.0.1",),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "missing header: x-uagents-address", "message": "Multiple handlers found for REST endpoint."}',  # noqa: E501
                }
            ),
        ]
    )

    # adding header should route correctly
    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await bureau._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-bureau",
                "client": ("127.0.0.1",),
                "headers": [(b"x-uagents-address", bob.address.encode())],
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"text": "bob response"}',
                }
            ),
        ]
    )


@pytest.mark.order(8)
async def test_rest_get_with_query_params_success():
    """Test GET request with query parameters using Request model"""

    @agent.on_rest_get("/get-params", Request, Response)
    async def _(ctx: Context, req: Request) -> Response:
        return Response(text=f"Received: {req.text}")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-params",
                "query_string": b"text=hello",
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"text": "Received: hello"}',
                }
            ),
        ]
    )


@pytest.mark.order(9)
async def test_rest_get_missing_required_params():
    """Test GET request with missing required parameters - should return 400"""

    @agent.on_rest_get("/get-missing", Request, Response)
    async def _(ctx: Context, req: Request) -> Response:
        return Response(text=f"Received: {req.text}")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-missing",
                "query_string": b"",  # Missing 'text' parameter
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"loc": ["text"], "msg": "field required", '
                    b'"type": "value_error.missing"}',
                }
            ),
        ]
    )


@pytest.mark.order(10)
async def test_rest_get_url_encoded_params():
    """Test GET request with URL-encoded special characters"""

    @agent.on_rest_get("/get-encoded", Request, Response)
    async def _(ctx: Context, req: Request) -> Response:
        return Response(text=f"Received: {req.text}")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-encoded",
                "query_string": b"text=hello%20world",
                "client": ("127.0.0.1", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"text": "Received: hello world"}',
                }
            ),
        ]
    )
