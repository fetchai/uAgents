# pylint: disable=protected-access
import asyncio
import json
import unittest
import uuid
from unittest.mock import AsyncMock, call, patch

from uagents_core.envelope import Envelope
from uagents_core.identity import generate_user_address

from uagents import Agent, Model
from uagents.communication import enclose_response
from uagents.config import RESPONSE_TIME_HINT_SECONDS
from uagents.crypto import Identity


class Message(Model):
    message: str


class TestServer(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.agent = Agent(name="alice", seed="alice recovery password")
        self.bob = Agent(name="bob", seed="bob recovery password")
        return super().setUp()

    async def mock_process_sync_message(self, sender: str, msg: Model):
        while True:
            if sender in self.agent._server._queries:
                self.agent._server._queries[sender].set_result(
                    (msg.model_dump_json(), Model.build_schema_digest(msg))
                )
                return

    async def test_message_success(self):
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=self.agent.address,
            session=uuid.uuid4(),
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())
        env.sign(self.bob._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/json"},
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
                )
            ]
        )

    async def test_message_success_unsigned(self):
        message = Message(message="hello")
        user = generate_user_address()
        session = uuid.uuid4()
        env = Envelope(
            version=1,
            sender=user,
            target=self.agent.address,
            session=session,
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/json"},
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
                )
            ]
        )

    async def test_message_success_sync_unsigned(self):
        message = Message(message="hello")
        reply = Message(message="hey")
        user = generate_user_address()
        session = uuid.uuid4()
        env = Envelope(
            version=1,
            sender=user,
            target=self.agent.address,
            session=session,
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())
        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await asyncio.gather(
                asyncio.create_task(
                    self.agent._server(
                        scope={
                            "type": "http",
                            "method": "POST",
                            "path": "/submit",
                            "headers": {
                                b"content-type": b"application/json",
                                b"x-uagents-connection": b"sync",
                            },
                        },
                        receive=None,
                        send=mock_send,
                    )
                ),
                asyncio.create_task(self.mock_process_sync_message(user, reply)),
            )
        response = enclose_response(reply, self.agent.address, session, user)
        formatted = json.loads(response)
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
                        "body": json.dumps(formatted).encode(),
                    }
                ),
            ]
        )

    async def test_message_success_sync_signed(self):
        message = Message(message="hello")
        reply = Message(message="hey")
        session = uuid.uuid4()
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=self.agent.address,
            session=session,
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())
        env.sign(self.bob._identity)
        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await asyncio.gather(
                asyncio.create_task(
                    self.agent._server(
                        scope={
                            "type": "http",
                            "method": "POST",
                            "path": "/submit",
                            "headers": {
                                b"content-type": b"application/json",
                                b"x-uagents-connection": b"sync",
                            },
                        },
                        receive=None,
                        send=mock_send,
                    )
                ),
                asyncio.create_task(
                    self.mock_process_sync_message(self.bob.address, reply)
                ),
            )
        response = enclose_response(
            reply, self.agent.address, session, self.bob.address
        )
        formatted = json.loads(response)
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
                        "body": json.dumps(formatted).encode(),
                    }
                ),
            ]
        )

    async def test_message_fail_wrong_path(self):
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=self.agent.address,
            session=uuid.uuid4(),
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())
        env.sign(self.bob._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/bad/path",
                    "headers": {b"content-type": b"application/json"},
                },
                receive=None,
                send=mock_send,
            )
        mock_send.assert_has_calls(
            [
                call(
                    {
                        "type": "http.response.start",
                        "status": 404,
                        "headers": [[b"content-type", b"application/json"]],
                    }
                ),
                call(
                    {
                        "type": "http.response.body",
                        "body": b'{"error": "not found"}',
                    }
                ),
            ]
        )

    async def test_message_fail_wrong_headers(self):
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=self.agent.address,
            session=uuid.uuid4(),
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())
        env.sign(self.bob._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/badapp"},
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
                        "body": b'{"error": "invalid content-type"}',
                    }
                ),
            ]
        )

    async def test_message_fail_bad_data(self):
        message = Message(message="hello")
        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = message.model_dump_json().encode()
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/json"},
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
                        "body": b'{"error": "contents do not match envelope schema"}',
                    }
                ),
            ]
        )

    async def test_message_fail_unsigned(self):
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=self.agent.address,
            session=uuid.uuid4(),
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/json"},
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
                        "body": b'{"error": "Envelope signature is missing"}',
                    }
                ),
            ]
        )

    async def test_message_fail_verify(self):
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=self.agent.address,
            session=uuid.uuid4(),
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())
        env.sign(self.agent._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/json"},
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
                        "body": b'{"error": "Signature verification failed"}',
                    }
                ),
            ]
        )

    async def test_message_fail_dispatch(self):
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=generate_user_address(),
            session=uuid.uuid4(),
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())
        env.sign(self.bob._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.model_dump_json().encode()
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/json"},
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
                        "body": b'{"error": "unable to route envelope"}',
                    }
                ),
            ]
        )

    async def test_message_success_streamed_body(self):
        """A body arriving in multiple chunks under the limit must be read normally."""
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=generate_user_address(),
            target=self.agent.address,
            session=uuid.uuid4(),
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())

        body = env.model_dump_json().encode()
        chunks = [body[:10], body[10:20], body[20:]]

        async def receive():
            chunk = chunks.pop(0)
            return {
                "type": "http.request",
                "body": chunk,
                "more_body": bool(chunks),
            }

        mock_send = AsyncMock()
        await self.agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/submit",
                "headers": {b"content-type": b"application/json"},
            },
            receive=receive,
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
                        "body": b"{}",
                    }
                ),
            ]
        )

    async def test_message_fail_body_too_large(self):
        """An oversized request body must be rejected before being fully buffered."""
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=generate_user_address(),
            target=self.agent.address,
            session=uuid.uuid4(),
            schema_digest=Model.build_schema_digest(message),
        )
        env.encode_payload(message.model_dump_json())

        body = env.model_dump_json().encode()
        chunks = [body[:16], body[16:-1], body[-1:]]

        async def receive():
            chunk = chunks.pop(0)
            return {
                "type": "http.request",
                "body": chunk,
                "more_body": bool(chunks),
            }

        self.agent._server._max_body_size = 16

        mock_send = AsyncMock()
        await self.agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/submit",
                "headers": {b"content-type": b"application/json"},
            },
            receive=receive,
            send=mock_send,
        )
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
        # reading stopped as soon as the limit was exceeded:
        # the last chunk was never received or buffered
        self.assertEqual(len(chunks), 1)

    async def test_request_fail_missing_header(self):
        mock_send = AsyncMock()
        await self.agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/submit",
                "headers": {},
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
                        "body": b'{"error": "missing header: content-type"}',
                    }
                ),
            ]
        )

    async def test_request_fail_no_contents(self):
        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = None
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/json"},
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
                        "body": b'{"error": "empty or invalid payload"}',
                    }
                ),
            ]
        )

    async def test_request_fail_invalid_json(self):
        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = b'{"bad", "json"}'
            await self.agent._server(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/submit",
                    "headers": {b"content-type": b"application/json"},
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
                        "body": b'{"error": "empty or invalid payload"}',
                    }
                ),
            ]
        )

    async def test_request_from_browser(self):
        mock_send = AsyncMock()
        await self.agent._server(
            scope={
                "type": "http",
                "method": "POST",
                "path": "/submit",
                "headers": {b"User-Agent": b"Mozilla/5.0"},
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
                        "body": b'{"status": "OK - Agent is running"}',
                    }
                ),
            ]
        )

    async def test_head_no_address_header(self):
        mock_send = AsyncMock()
        await self.agent._server(
            scope={
                "type": "http",
                "method": "HEAD",
                "path": "/submit",
                "headers": {},
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
                        "headers": [
                            [b"x-uagents-status", b"indeterminate"],
                        ],
                    }
                ),
            ]
        )

    async def test_head_agent_ready(self):
        mock_send = AsyncMock()
        await self.agent._server(
            scope={
                "type": "http",
                "method": "HEAD",
                "path": "/submit",
                "headers": {b"x-uagents-address": self.agent.address.encode()},
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
                        "headers": [
                            [b"x-uagents-status", b"ready"],
                            [
                                b"x-uagents-response-time-hint",
                                str(RESPONSE_TIME_HINT_SECONDS).encode(),
                            ],
                        ],
                    }
                ),
            ]
        )

    async def test_head_agent_not_ready(self):
        mock_send = AsyncMock()
        await self.agent._server(
            scope={
                "type": "http",
                "method": "HEAD",
                "path": "/submit",
                "headers": {b"x-uagents-address": Identity.generate().address.encode()},
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
                        "headers": [
                            [b"x-uagents-status", b"not-ready"],
                        ],
                    }
                ),
            ]
        )


if __name__ == "__main__":
    unittest.main()
