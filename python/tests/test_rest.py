# pylint: disable=protected-access
from unittest.mock import AsyncMock, call, patch

import pytest

from uagents import Agent, Bureau, Context, Model
from uagents.config import DEFAULT_MAX_BODY_SIZE_BYTES

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
    @agent.on_rest_get("/get-success", Response)
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

    @agent.on_rest_get("/get-body-wrong", Response)
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
                "path": "/messages",
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
    @agent.on_rest_get("/get-bureau", Response)
    async def _(_ctx: Context):
        return Response(text="Hi there!")

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
                    "body": b'{"text": "Hi there!"}',
                }
            ),
        ]
    )

    # bureau adds second agent with same endpoint, should return 400
    @bob.on_rest_get("/get-bureau", Response)
    async def _(_ctx: Context):
        return Response(text="Hi too!")

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
                    "body": b'{"text": "Hi too!"}',
                }
            ),
        ]
    )


@pytest.mark.order(8)
async def test_rest_get_forbidden_for_non_local_client():
    @agent.on_rest_get("/get-private", Response)
    async def _(_ctx: Context):
        return Response(text="Hi there!")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-private",
                "client": ("203.0.113.10", 1234),
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


@pytest.mark.order(9)
async def test_rest_post_forbidden_for_non_local_client():
    @agent.on_rest_post("/post-private", Request, Response)
    async def _(_ctx: Context, req: Request):
        return Response(text=f"Received: {req.text}")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b'{"text": "Hello"}'
        await agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/post-private",
                "client": ("203.0.113.10", 1234),
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


@pytest.mark.order(10)
async def test_rest_get_public_endpoint_allows_non_local_client():
    @agent.on_rest_get("/get-public", Response, public=True)
    async def _(_ctx: Context):
        return Response(text="Hi there!")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-public",
                "client": ("203.0.113.10", 1234),
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


@pytest.mark.order(11)
async def test_rest_post_public_endpoint_allows_non_local_client():
    @agent.on_rest_post("/post-public", Request, Response, public=True)
    async def _(_ctx: Context, req: Request):
        return Response(text=f"Received: {req.text}")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b'{"text": "Hello"}'
        await agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/post-public",
                "client": ("203.0.113.10", 1234),
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


@pytest.mark.order(12)
async def test_rest_get_private_endpoint_allows_ipv6_loopback():
    @agent.on_rest_get("/get-private-v6", Response)
    async def _(_ctx: Context):
        return Response(text="Hi there!")

    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/get-private-v6",
                "client": ("::1", 1234),
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


@pytest.mark.order(13)
async def test_agent_info_endpoint_is_public():
    mock_send = AsyncMock()
    with patch("uagents.asgi._read_asgi_body") as mock_receive:
        mock_receive.return_value = b""
        await agent._server(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/agent_info",
                "client": ("203.0.113.10", 1234),
            },
            receive=None,
            send=mock_send,
        )
    mock_send.assert_any_call(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )


@pytest.mark.order(1000)
async def test_rest_post_body_too_large():
    @agent.on_rest_post("/post-too-large", Request, Response)
    async def _(_ctx: Context, req: Request):
        return Response(text=f"Received: {req.text}")

    # shrink the limit so the test doesn't have to push megabytes through
    agent._server._max_body_size = 16

    msgs = [
        {"body": b"a" * 16, "more_body": True},
        {"body": b"b" * 16, "more_body": True},
        {"body": b"c" * 16, "more_body": False},
    ]
    msgs_iter = iter(msgs)

    async def receive():
        return next(msgs_iter)

    mock_send = AsyncMock()
    try:
        await agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/post-too-large",
                "client": ("127.0.0.1", 1234),
            },
            receive=receive,
            send=mock_send,
        )
    finally:
        # restore the default for the shared module-level agent
        agent._server._max_body_size = DEFAULT_MAX_BODY_SIZE_BYTES
    mock_send.assert_has_calls(
        [
            call(
                {
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [[b"content-type", b"application/json"]],
                }
            ),
            call(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "request body too large"}',
                }
            ),
        ]
    )
    # reading must have stopped as soon as the limit was exceeded
    assert next(msgs_iter, None) is not None
