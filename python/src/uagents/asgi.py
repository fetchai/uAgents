import asyncio
import json
from datetime import datetime
from logging import Logger
from typing import Dict, Optional

import pydantic
import uvicorn
from requests.structures import CaseInsensitiveDict

from uagents.config import get_logger, RESPONSE_TIME_HINT_SECONDS
from uagents.crypto import is_user_address
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope
from uagents.models import ErrorMessage
from uagents.query import enclose_response_raw


HOST = "0.0.0.0"


async def _read_asgi_body(receive):
    """
    Read the entire body of an ASGI message.
    """
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)

    return body


class ASGIServer:
    """
    ASGI server for receiving incoming envelopes.
    """

    def __init__(
        self,
        port: int,
        loop: asyncio.AbstractEventLoop,
        queries: Dict[str, asyncio.Future],
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the ASGI server.

        Args:
            port (int): The port to listen on.
            loop (asyncio.AbstractEventLoop): The event loop to use.
            queries (Dict[str, asyncio.Future]): The dictionary of queries to resolve.
            logger (Optional[Logger]): The logger to use.
        """
        self._port = int(port)
        self._loop = loop
        self._queries = queries
        self._logger = logger or get_logger("server")
        self._server = None

    @property
    def server(self):
        """
        Property to access the underlying uvicorn server.

        Returns: The server.
        """
        return self._server

    async def handle_readiness_probe(self, headers: CaseInsensitiveDict, send):
        """
        Handle a readiness probe sent via the HEAD method.
        """
        if b"x-uagents-address" not in headers:
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        [b"x-uagents-status", b"indeterminate"],
                    ],
                }
            )
        else:
            address = headers[b"x-uagents-address"].decode()
            if not dispatcher.contains(address):
                await send(
                    {
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [
                            [b"x-uagents-status", b"not-ready"],
                        ],
                    }
                )
            else:
                await send(
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
                )
        return

    async def handle_missing_content_type(self, headers: CaseInsensitiveDict, send):
        """
        Handle missing content type header.
        """
        # if connecting from browser, return a 200 OK
        if b"user-agent" in headers:
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
                    "body": b'{"status": "OK - Agent is running"}',
                }
            )
        else:  # otherwise, return a 400 Bad Request
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
                    "body": b'{"error": "missing header: content-type"}',
                }
            )

    async def serve(self):
        """
        Start the server.
        """
        config = uvicorn.Config(self, host=HOST, port=self._port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._logger.info(
            f"Starting server on http://{HOST}:{self._port} (Press CTRL+C to quit)"
        )
        await self._server.serve()

    async def __call__(
        self, scope, receive, send
    ):  #  pylint: disable=too-many-branches
        """
        Handle an incoming ASGI message, dispatching the envelope to the appropriate handler,
        and waiting for any queries to be resolved.
        """
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

        headers = CaseInsensitiveDict(scope.get("headers", {}))

        request_method = scope["method"]
        if request_method == "HEAD":
            await self.handle_readiness_probe(headers, send)
            return

        if b"content-type" not in headers:
            await self.handle_missing_content_type(headers, send)
            return

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
                {
                    "type": "http.response.body",
                    "body": b'{"error": "invalid content-type"}',
                }
            )
            return

        # read the entire payload
        raw_contents = await _read_asgi_body(receive)

        try:
            contents = json.loads(raw_contents.decode())
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
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
                    "body": b'{"error": "empty or invalid payload"}',
                }
            )
            return

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
                {
                    "type": "http.response.body",
                    "body": b'{"error": "contents do not match envelope schema"}',
                }
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
                    "body": b'{"error": "signature verification failed"}',
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
            env.sender, env.target, env.schema_digest, env.decode_payload(), env.session
        )

        # wait for any queries to be resolved
        if expects_response:
            response_msg, schema_digest = await self._queries[env.sender]
            if env.expires is not None:
                if datetime.now() > datetime.fromtimestamp(env.expires):
                    response_msg = ErrorMessage(error="Query envelope expired")
            sender = env.target
            response = enclose_response_raw(
                response_msg, schema_digest, sender, str(env.session)
            )
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
