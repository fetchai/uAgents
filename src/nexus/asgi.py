import asyncio
import json
from typing import Dict

import pydantic
import uvicorn

from nexus.crypto import generate_query_user
from nexus.dispatch import dispatcher
from nexus.envelope import Envelope


async def _read_asgi_body(receive):
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)

    return body


class ASGIServer:
    def __init__(
        self,
        port: int,
        loop: asyncio.AbstractEventLoop,
        queries: Dict[str, asyncio.Future],
    ):
        self._port = int(port)
        self._loop = loop
        self._queries = queries

    async def serve(self):
        config = uvicorn.Config(self, host="0.0.0.0", port=self._port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return  # lifespan events not implemented

        assert scope["type"] == "http"

        if scope["path"] != "/submit":
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": b'{"error": "not found"}'}
            )
            return

        headers = dict(scope.get("headers", {}))
        if headers[b"content-type"] != b"application/json":
            await send(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": b'{"error": "invalid format"}'}
            )
            return

        is_query = b"uAgents-Query" in headers
        if is_query:
            # uagents_headers = headers.get(b"uAgents-Query")
            
            # Generate a temporary address
            user_address = generate_query_user()

            # Add a future that will be resolved once the query is answered
            self._queries[user_address] = asyncio.Future()

        # read the entire payload
        raw_contents = await _read_asgi_body(receive)
        contents = json.loads(raw_contents.decode())

        try:
            env = Envelope.parse_obj(contents)
        except pydantic.ValidationError:
            await send(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": b'{"error": "invalid format"}'}
            )
            return

        if not env.verify():
            await send(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "unable to verify payload"}',
                }
            )
            return

        if not dispatcher.contains(env.target):
            await send(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "unable to route envelope"}',
                }
            )
            return

        await dispatcher.dispatch(
            env.sender, env.target, env.protocol, env.decode_payload()
        )

        # wait for any queries to be resolved
        response = "{}"
        if is_query:
            response = await self._queries[user_address]

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/json"],
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": response.encode(),
            }
        )
