# pylint: disable=protected-access
from unittest.mock import AsyncMock, call, patch

import pytest

from uagents import Agent, Context, Model

pytestmark = pytest.mark.asyncio


class Request(Model):
    text: str


class Response(Model):
    text: str


agent = Agent(name="alice")


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
                    "body": b'[\n  {\n    "loc": [\n      "text"\n    ],\n    "msg": "field required",\n    "type": "value_error.missing"\n  }\n]',  # noqa: E501
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
