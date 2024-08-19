import asyncio
import json
from datetime import datetime
from logging import Logger
from typing import Dict, Optional, Tuple, Type

import uvicorn
from pydantic import ValidationError
from pydantic.v1 import ValidationError as ValidationErrorV1
from requests.structures import CaseInsensitiveDict

from uagents.communication import enclose_response_raw
from uagents.config import RESPONSE_TIME_HINT_SECONDS
from uagents.context import ERROR_MESSAGE_DIGEST, Context
from uagents.crypto import is_user_address
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope
from uagents.models import ErrorMessage, Model
from uagents.rest import RestHandler, RestHandlerDetails, RestHandlerMap, RestMethod
from uagents.utils import get_logger

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
        ctx: Context,
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
        self._rest_handlers: RestHandlerMap = {}
        self._logger = logger or get_logger("server")
        self._server = None
        self._ctx = ctx

    @property
    def server(self):
        """
        Property to access the underlying uvicorn server.

        Returns: The server.
        """
        return self._server

    def add_rest_endpoint(
        self,
        method: RestMethod,
        endpoint: str,
        handler: RestHandler,
        request: Optional[Type[Model]],
        response: Type[Model],
    ):
        self._rest_handlers[(method, endpoint)] = RestHandlerDetails(
            method=method,
            handler=handler,
            request_model=request,
            response_model=response,
        )

    def has_rest_endpoint(self, method: RestMethod, endpoint: str) -> bool:
        return (method, endpoint) in self._rest_handlers

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
        try:
            await self._server.serve()
        except KeyboardInterrupt:
            self._logger.info("Shutting down server")

    async def _handle_rest(self, rest_handler: RestHandlerDetails, send, receive):
        # read all the data
        raw_contents = await _read_asgi_body(receive)
        args: Tuple = (self._ctx,)

        if rest_handler.method == "POST" and rest_handler.request_model is not None:
            if not raw_contents:
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
                        "body": b'{"error": "no request body found"}',
                    }
                )
                return

            try:
                received_request: Model = (
                    rest_handler.request_model.model_validate_json(raw_contents)
                )
                args = (self._ctx, received_request)
            except ValidationErrorV1 as err:
                self._logger.debug(f"Failed to validate REST request: {err}")
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
                        "body": err.json().encode(),
                    }
                )
                return

        # call the handler
        handler_response = await rest_handler.handler(*args)  # type: ignore

        # ensure the response is parsed as valid
        try:
            validated_response = rest_handler.response_model.parse_obj(handler_response)
        except ValidationErrorV1 as err:
            self._logger.debug(f"Failed to validate REST response: {err}")
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": err.json().encode(),
                }
            )
            return

        # return the validated response
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
            {"type": "http.response.body", "body": validated_response.json().encode()}
        )

    async def __call__(self, scope, receive, send):  #  pylint: disable=too-many-branches
        """
        Handle an incoming ASGI message, dispatching the envelope to the appropriate handler,
        and waiting for any queries to be resolved.
        """
        if scope["type"] == "lifespan":
            return  # lifespan events not implemented

        assert scope["type"] == "http"

        request_method = scope["method"]
        rest_handler = self._rest_handlers.get((request_method, scope["path"]))

        is_submit = scope["path"] == "/submit"
        is_bad = not is_submit and rest_handler is None

        # if this is a request handler then we should handle it as such
        if rest_handler is not None:
            await self._handle_rest(rest_handler, send, receive)
            return

        if is_bad:
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
            env = Envelope.model_validate(contents)
        except ValidationError:
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

        expects_response = headers.get(b"x-uagents-connection") == b"sync"

        if expects_response:
            # Add a future that will be resolved once the query is answered
            self._queries[env.sender] = asyncio.Future()

        if not is_user_address(env.sender):  # verify signature if sent from agent
            try:
                env.verify()
            except Exception as err:
                self._logger.warning(f"Failed to verify envelope: {err}")
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
            if (env.expires is not None) and (
                datetime.now() > datetime.fromtimestamp(env.expires)
            ):
                response_msg = ErrorMessage(
                    error="Query envelope expired"
                ).model_dump_json()
                schema_digest = ERROR_MESSAGE_DIGEST
            sender = env.target
            target = env.sender
            response = enclose_response_raw(
                response_msg, schema_digest, sender, env.session, target=target
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
