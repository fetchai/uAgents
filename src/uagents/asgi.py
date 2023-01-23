import asyncio
import json
from datetime import datetime
from typing import Dict

import pydantic
import uvicorn

from uagents.crypto import is_user_address
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope
from uagents.models import Model, ErrorMessage
from uagents.query import enclose_response


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
        if b"application/json" not in headers[b"content-type"]:
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

        # read the entire payload
        raw_contents = await _read_asgi_body(receive)
        contents = json.loads(raw_contents.decode())

        try:
            env: Envelope = Envelope.parse_obj(contents)
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

        expects_response = b"sync" == headers.get(b"x-uagents-connection")
        do_verify = not is_user_address(env.sender)

        if expects_response:
            # Add a future that will be resolved once the query is answered
            self._queries[env.sender] = asyncio.Future()

        if do_verify and env.verify() is False:
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
        if expects_response:
            response_msg: Model = await self._queries[env.sender]
            if env.expires is not None:
                if datetime.now() > datetime.fromtimestamp(env.expires):
                    response_msg = ErrorMessage("Query envelope expired")
            sender = env.target
            response = enclose_response(response_msg, sender, env.session)
        else:
            response = "{}"

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
