import asyncio
import json
from datetime import datetime
from logging import Logger
from typing import (
    Dict,
    Optional,
    Tuple,
    Type,
)

import uvicorn
from pydantic import ValidationError
from pydantic.v1 import ValidationError as ValidationErrorV1
from requests.structures import CaseInsensitiveDict

from uagents.communication import enclose_response_raw
from uagents.config import RESPONSE_TIME_HINT_SECONDS
from uagents.context import ERROR_MESSAGE_DIGEST
from uagents.crypto import is_user_address
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope
from uagents.models import ErrorMessage, Model
from uagents.types import RestHandlerDetails, RestMethod
from uagents.utils import get_logger

HOST = "0.0.0.0"

RESERVED_ENDPOINTS = ["/submit", "/messages", "/agent_info"]


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
        self._rest_handler_map: Dict[
            Tuple[str, RestMethod, str], RestHandlerDetails
        ] = {}
        self._logger = logger or get_logger("server")
        self._server = None

    @property
    def server(self):
        """
        Property to access the underlying uvicorn server.

        Returns: The server.
        """
        return self._server

    def add_rest_endpoint(
        self,
        address: str,
        method: RestMethod,
        endpoint: str,
        request: Optional[Type[Model]],
        response: Type[Model],
    ):
        """
        Add a REST endpoint to the server.
        """
        self._rest_handler_map[(address, method, endpoint)] = RestHandlerDetails(
            method=method,
            endpoint=endpoint,
            request_model=request,
            response_model=response,
        )

    def has_rest_endpoint(self, method: RestMethod, endpoint: str) -> bool:
        """
        Check if the server has a REST endpoint registered.
        """
        if endpoint in RESERVED_ENDPOINTS:
            self._logger.warning(f"Endpoint {endpoint} is reserved")
            return True
        return any(
            meth == method and end == endpoint
            for sink, meth, end in self._rest_handler_map
        )

    def _get_rest_handler_details(
        self, method: RestMethod, endpoint: str
    ) -> Dict[str, RestHandlerDetails]:
        handlers = {}
        for sink, meth, end in self._rest_handler_map:
            if meth == method and end == endpoint:
                handlers[sink] = self._rest_handler_map[(sink, meth, end)]
        return handlers

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
        config = uvicorn.Config(
            self,
            host=HOST,
            port=self._port,
            log_level="warning",
            forwarded_allow_ips="*",
            headers=[
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "*"),
                ("Access-Control-Allow-Credentials", "false"),
            ],
        )
        self._server = uvicorn.Server(config)
        self._logger.info(
            f"Starting server on http://{HOST}:{self._port} (Press CTRL+C to quit)"
        )
        try:
            await self._server.serve()
        except KeyboardInterrupt:
            self._logger.info("Shutting down server")

    async def _handle_rest(
        self,
        headers: CaseInsensitiveDict,
        handlers: Dict[str, RestHandlerDetails],
        send,
        receive,
    ):
        raw_contents = await _read_asgi_body(receive)
        received_request: Optional[Model] = None
        if len(handlers) > 1:
            if b"x-uagents-address" not in headers:
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
                        "body": b"""{
                            "error": "missing header: x-uagents-address",
                            "message": "Multiple handlers found for REST endpoint."
                            }""",
                    }
                )
                return
            destination = headers[b"x-uagents-address"].decode()
            rest_handler = handlers.get(destination)
        else:
            destination, rest_handler = handlers.popitem()

        if not rest_handler:
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
                {
                    "type": "http.response.body",
                    "body": b'{"error": "not found"}',
                }
            )
            return

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
                        "body": b'{"error": "No request body found"}',
                    }
                )
                return

            try:
                received_request = rest_handler.request_model.model_validate_json(
                    raw_contents
                )
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

        # get & call the handler
        handler_response = await dispatcher.dispatch_rest(
            destination=destination,
            method=rest_handler.method,
            endpoint=rest_handler.endpoint,
            message=received_request,
        )

        # ensure the response is parsed as valid
        try:
            if not isinstance(handler_response, dict) and not isinstance(
                handler_response, rest_handler.response_model
            ):
                raise ValueError(
                    {"error": "Handler response must be a dict or a model"}
                )
            validated_response = rest_handler.response_model.parse_obj(handler_response)
        except (ValidationErrorV1, ValueError) as err:
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
                    "body": b'{"error": "Handler response does not match response schema."}',
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
        scope_type = scope["type"]
        if scope_type == "lifespan" or scope_type != "http":
            return  # lifespan events not implemented and only handle http

        headers = CaseInsensitiveDict(scope.get("headers", {}))
        request_method = scope["method"]
        request_path = scope["path"]

        # check if the request is for a REST endpoint
        handlers = self._get_rest_handler_details(request_method, request_path)
        if handlers:
            if "127.0.0.1" not in scope["client"]:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [
                            [b"content-type", b"application/json"],
                        ],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": b'{"error": "forbidden"}',
                    }
                )
                return
            await self._handle_rest(headers, handlers, send, receive)
            return

        # check if the request is for agent communication and reject if not
        if request_path != "/submit":
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

        await dispatcher.dispatch_msg(
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
