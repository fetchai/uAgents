# pylint: disable=protected-access
import asyncio
import unittest
import uuid
from unittest.mock import patch, AsyncMock, call

from uagents import Agent, Model
from uagents.envelope import Envelope
from uagents.crypto import generate_user_address
from uagents.query import enclose_response


class Message(Model):
    message: str


class TestServer(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.agent = Agent(name="alice", seed="alice recovery password")
        self.bob = Agent(name="bob", seed="bob recovery password")
        self.loop: asyncio.BaseEventLoop = self._asyncioTestLoop
        return super().setUp()

    async def mock_process_sync_message(self, sender: str, msg: Model):
        while True:
            if sender in self.agent._server._queries:
                self.agent._server._queries[sender].set_result(msg)
                return

    async def test_message_success(self):
        message = Message(message="hello")
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=self.agent.address,
            session=uuid.uuid4(),
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())
        env.sign(self.bob._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await self.agent._server(
                scope=dict(
                    type="http",
                    path="/submit",
                    headers={b"content-type": b"application/json"},
                ),
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
                        "body": b"{}",
                    }
                ),
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
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await self.agent._server(
                scope=dict(
                    type="http",
                    path="/submit",
                    headers={b"content-type": b"application/json"},
                ),
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
                        "body": b"{}",
                    }
                ),
            ]
        )

    async def test_message_success_sync(self):
        message = Message(message="hello")
        reply = Message(message="hey")
        user = generate_user_address()
        session = uuid.uuid4()
        env = Envelope(
            version=1,
            sender=user,
            target=self.agent.address,
            session=session,
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())
        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await asyncio.gather(
                self.loop.create_task(
                    self.agent._server(
                        scope=dict(
                            type="http",
                            path="/submit",
                            headers={
                                b"content-type": b"application/json",
                                b"x-uagents-connection": b"sync",
                            },
                        ),
                        receive=None,
                        send=mock_send,
                    )
                ),
                self.loop.create_task(self.mock_process_sync_message(user, reply)),
            )
        response = enclose_response(reply, self.agent.address, session)
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
                        "body": response.encode(),
                    }
                ),
            ]
        )

    async def test_message_success_sync_unsigned(self):
        message = Message(message="hello")
        reply = Message(message="hey")
        session = uuid.uuid4()
        env = Envelope(
            version=1,
            sender=self.bob.address,
            target=self.agent.address,
            session=session,
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())
        env.sign(self.bob._identity)
        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await asyncio.gather(
                self.loop.create_task(
                    self.agent._server(
                        scope=dict(
                            type="http",
                            path="/submit",
                            headers={
                                b"content-type": b"application/json",
                                b"x-uagents-connection": b"sync",
                            },
                        ),
                        receive=None,
                        send=mock_send,
                    )
                ),
                self.loop.create_task(
                    self.mock_process_sync_message(self.bob.address, reply)
                ),
            )
        response = enclose_response(reply, self.agent.address, session)
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
                        "body": response.encode(),
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
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())
        env.sign(self.bob._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await self.agent._server(
                scope=dict(
                    type="http",
                    path="/bad/path",
                    headers={b"content-type": b"application/json"},
                ),
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
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())
        env.sign(self.bob._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await self.agent._server(
                scope=dict(
                    type="http",
                    path="/submit",
                    headers={b"content-type": b"application/badapp"},
                ),
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
                        "body": b'{"error": "invalid format"}',
                    }
                ),
            ]
        )

    async def test_message_fail_bad_data(self):
        message = Message(message="hello")
        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = message.json().encode()
            await self.agent._server(
                scope=dict(
                    type="http",
                    path="/submit",
                    headers={b"content-type": b"application/json"},
                ),
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
                        "body": b'{"error": "invalid format"}',
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
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await self.agent._server(
                scope=dict(
                    type="http",
                    path="/submit",
                    headers={b"content-type": b"application/json"},
                ),
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
                        "body": b'{"error": "unable to verify payload"}',
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
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())
        env.sign(self.agent._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await self.agent._server(
                scope=dict(
                    type="http",
                    path="/submit",
                    headers={b"content-type": b"application/json"},
                ),
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
                        "body": b'{"error": "unable to verify payload"}',
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
            protocol=Model.build_schema_digest(message),
        )
        env.encode_payload(message.json())
        env.sign(self.bob._identity)

        mock_send = AsyncMock()
        with patch("uagents.asgi._read_asgi_body") as mock_receive:
            mock_receive.return_value = env.json().encode()
            await self.agent._server(
                scope=dict(
                    type="http",
                    path="/submit",
                    headers={b"content-type": b"application/json"},
                ),
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


if __name__ == "__main__":
    unittest.main()
