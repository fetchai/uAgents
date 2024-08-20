# pylint: disable=protected-access
import unittest
from unittest.mock import AsyncMock, call, patch

from uagents import Agent, Context, Model


class Request(Model):
    text: str


class Response(Model):
    text: str


class TestServer(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.agent = Agent(name="alice", seed="alice recovery password")
        return super().setUp()

    # async def test_rest_get_success(self):
    #     @self.agent.on_rest_get("/get", Response)
    #     async def _(_ctx: Context):
    #         return Response(text="Hi there!")

    #     mock_send = AsyncMock()
    #     with patch("uagents.asgi._read_asgi_body") as mock_receive:
    #         mock_receive.return_value = b""
    #         await self.agent._server(
    #             scope={
    #                 "type": "http",
    #                 "method": "GET",
    #                 "path": "/get",
    #             },
    #             receive=None,
    #             send=mock_send,
    #         )
    #     mock_send.assert_has_calls(
    #         [
    #             call(
    #                 {
    #                     "type": "http.response.start",
    #                     "status": 200,
    #                     "headers": [[b"content-type", b"application/json"]],
    #                 }
    #             ),
    #             call(
    #                 {
    #                     "type": "http.response.body",
    #                     "body": b'{"text": "Hi there!"}',
    #                 }
    #             ),
    #         ]
    #     )

    # async def test_rest_post_success(self):
    #     @self.agent.on_rest_post("/post", Request, Response)
    #     async def _(_ctx: Context, req: Request):
    #         return Response(text=f"Received: {req.text}")

    #     mock_send = AsyncMock()
    #     with patch("uagents.asgi._read_asgi_body") as mock_receive:
    #         mock_receive.return_value = b'{"text": "Hello"}'
    #         await self.agent._server(
    #             scope={
    #                 "type": "http",
    #                 "method": "POST",
    #                 "path": "/post",
    #             },
    #             receive=None,
    #             send=mock_send,
    #         )
    #     mock_send.assert_has_calls(
    #         [
    #             call(
    #                 {
    #                     "type": "http.response.start",
    #                     "status": 200,
    #                     "headers": [[b"content-type", b"application/json"]],
    #                 }
    #             ),
    #             call(
    #                 {
    #                     "type": "http.response.body",
    #                     "body": b'{"text": "Received: Hello"}',
    #                 }
    #             ),
    #         ]
    #     )

    async def test_rest_post_fail_no_body(self):
        @self.agent.on_rest_post("/post", Request, Response)
        async def _(_ctx: Context, req: Request):
            return Response(text=f"Received: {req.text}")

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = b""
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/post",
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

    async def test_rest_post_fail_invalid_body(self):
        @self.agent.on_rest_post("/post", Request, Response)
        async def _(_ctx: Context, req: Request):
            return Response(text=f"Received: {req.text}")

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = b'{"invalid": "body"}'
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/post",
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

    async def test_rest_post_fail_invalid_response(self):
        wrong_response = {"obviously_wrong": "Oh no!"}
        wrong_response_model = Request(text="Hello")

        @self.agent.on_rest_post("/post", Request, Response)
        async def _(_ctx: Context, req: Request):
            return wrong_response

        @self.agent.on_rest_get("/get", Response)
        async def _(_ctx: Context):
            return wrong_response_model

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = b'{"text": "Hello"}'
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/post",
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
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "GET",
                    "path": "/get",
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


if __name__ == "__main__":
    unittest.main()
