import asyncio
import json
from datetime import datetime, timezone
from logging import Logger
from typing import Any

import uvicorn
from pydantic import BaseModel, ValidationError
from pydantic.v1 import ValidationError as ValidationErrorV1
from pydantic.v1.error_wrappers import ErrorWrapper
from requests.structures import CaseInsensitiveDict
from uagents_core.envelope import Envelope
from uagents_core.identity import is_user_address
from uagents_core.models import ERROR_MESSAGE_DIGEST, ErrorMessage, Model

from uagents.communication import enclose_response_raw
from uagents.config import DEFAULT_ENVELOPE_TIMEOUT_SECONDS, RESPONSE_TIME_HINT_SECONDS
from uagents.dispatch import dispatcher
from uagents.types import RestHandlerDetails, RestMethod
from uagents.utils import get_logger

HOST = "0.0.0.0"

RESERVED_ENDPOINTS = ["/submit", "/messages", "/agent_info", "/connect", "/disconnect"]


async def _read_asgi_body(receive):
    """Read the entire body of an ASGI message."""
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)

    return body


class ASGIServer:
    """ASGI server for receiving incoming envelopes."""

    def __init__(
        self,
        port: int,
        loop: asyncio.AbstractEventLoop,
        queries: dict[str, asyncio.Future],
        logger: Logger | None = None,
    ):
        """
        Initialize the ASGI server.

        Args:
            port (int): The port to listen on.
            loop (asyncio.AbstractEventLoop): The event loop to use.
            queries (dict[str, asyncio.Future]): The dictionary of queries to resolve.
            logger (Logger | None): The logger to use.
        """
        self._port = int(port)
        self._loop = loop
        self._queries = queries
        self._rest_handler_map: dict[
            tuple[str, RestMethod, str], RestHandlerDetails
        ] = {}
        self._logger = logger or get_logger("server")
        self._server: uvicorn.Server | None = None

    @property
    def server(self) -> uvicorn.Server | None:
        """Property to access the underlying uvicorn server."""
        return self._server

    def add_rest_endpoint(
        self,
        address: str,
        method: RestMethod,
        endpoint: str,
        request: type[Model] | None,
        response: type[Model | BaseModel],
    ):
        """Add a REST endpoint to the server."""
        self._rest_handler_map[(address, method, endpoint)] = RestHandlerDetails(
            method=method,
            endpoint=endpoint,
            request_model=request,
            response_model=response,
        )

    def has_rest_endpoint(self, method: RestMethod, endpoint: str) -> bool:
        """Check if the server has a REST endpoint registered."""
        if endpoint in RESERVED_ENDPOINTS:
            self._logger.warning(f"Endpoint {endpoint} is reserved")
            return True
        return any(
            meth == method and end == endpoint
            for sink, meth, end in self._rest_handler_map
        )

    def _get_rest_handler_details(
        self, method: RestMethod, endpoint: str
    ) -> dict[str, RestHandlerDetails]:
        handlers = {}
        for sink, meth, end in self._rest_handler_map:
            if meth == method and end == endpoint:
                handlers[sink] = self._rest_handler_map[(sink, meth, end)]
        return handlers

    async def _asgi_send(
        self,
        send,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | ErrorWrapper | None = None,
    ):
        header = (
            [[k.encode(), v.encode()] for k, v in headers.items()]
            if headers is not None
            else [[b"content-type", b"application/json"]]
        )

        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": header,
            }
        )

        if body is None:
            encoded_body = (
                b"{}" if [[b"content-type", b"application/json"]] in header else b""
            )
        else:
            encoded_body = json.dumps(body).encode()

        await send({"type": "http.response.body", "body": encoded_body})

    async def handle_readiness_probe(self, headers: CaseInsensitiveDict, send):
        """Handle a readiness probe sent via the HEAD method."""
        if b"x-uagents-address" not in headers:
            await self._asgi_send(
                send=send, headers={"x-uagents-status": "indeterminate"}
            )
        else:
            address = headers[b"x-uagents-address"].decode()  # type: ignore
            if not dispatcher.contains(address):
                await self._asgi_send(
                    send=send, headers={"x-uagents-status": "not-ready"}
                )
            else:
                await self._asgi_send(
                    send=send,
                    headers={
                        "x-uagents-status": "ready",
                        "x-uagents-response-time-hint": str(RESPONSE_TIME_HINT_SECONDS),
                    },
                )

    async def handle_missing_content_type(self, headers: CaseInsensitiveDict, send):
        """Handle missing content type header."""
        # if connecting from browser, return a 200 OK
        if b"user-agent" in headers:
            await self._asgi_send(send=send, body={"status": "OK - Agent is running"})
        else:  # otherwise, return a 400 Bad Request
            await self._asgi_send(
                send=send,
                status_code=400,
                body={"error": "missing header: content-type"},
            )

    async def serve(self):
        """Start the server."""
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
        except (asyncio.CancelledError, KeyboardInterrupt):
            self._logger.info("Shutting down server...")

    async def _handle_rest(
        self,
        headers: CaseInsensitiveDict,
        handlers: dict[str, RestHandlerDetails],
        send,
        receive,
    ):
        raw_contents = await _read_asgi_body(receive)
        received_request: Model | None = None
        if len(handlers) > 1:
            if b"x-uagents-address" not in headers:
                await self._asgi_send(
                    send=send,
                    status_code=400,
                    body={
                        "error": "missing header: x-uagents-address",
                        "message": "Multiple handlers found for REST endpoint.",
                    },
                )
                return
            destination = headers[b"x-uagents-address"].decode()  # type: ignore
            rest_handler = handlers.get(destination)
        else:
            destination, rest_handler = handlers.popitem()

        if not rest_handler:
            await self._asgi_send(
                send=send, status_code=404, body={"error": "not found"}
            )
            return

        if rest_handler.method == "POST" and rest_handler.request_model is not None:
            if not raw_contents:
                await self._asgi_send(
                    send=send, status_code=400, body={"error": "No request body found"}
                )
                return

            try:
                received_request = rest_handler.request_model.model_validate_json(
                    raw_contents
                )
            except ValidationErrorV1 as err:
                e = dict(err.errors().pop())
                self._logger.debug(f"Failed to validate REST request: {e}")
                await self._asgi_send(send=send, status_code=400, body=e)
                return

        # get & call the handler
        handler_response: (
            dict[str, Any] | Model | None
        ) = await dispatcher.dispatch_rest(
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
            validated_response = rest_handler.response_model.model_validate(
                handler_response
            )
        except (ValidationErrorV1, ValueError) as err:
            self._logger.debug(f"Failed to validate REST response: {err}")
            await self._asgi_send(
                send=send,
                status_code=500,
                body={"error": "Handler response does not match response schema."},
            )
            return

        # return the validated response
        await self._asgi_send(send=send, body=validated_response.model_dump())

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

        # Handle OPTIONS preflight request for CORS
        if request_method == "OPTIONS":
            await self._asgi_send(send=send, status_code=204, headers={})
            return

        # check if the request is for a REST endpoint
        handlers: dict[str, RestHandlerDetails] = self._get_rest_handler_details(
            method=request_method, endpoint=request_path
        )
        if handlers:
            if (
                request_path in RESERVED_ENDPOINTS
                and "127.0.0.1" not in scope["client"]
            ):
                await self._asgi_send(
                    send=send, status_code=403, body={"error": "forbidden"}
                )
                return
            await self._handle_rest(headers, handlers, send, receive)
            return

        # check if the request is for agent communication and reject if not
        if request_path != "/submit":
            await self._asgi_send(
                send=send, status_code=404, body={"error": "not found"}
            )
            return

        if request_method == "HEAD":
            await self.handle_readiness_probe(headers, send)
            return

        if b"content-type" not in headers:
            await self.handle_missing_content_type(headers, send)
            return

        if b"application/json" not in headers[b"content-type"]:  # type: ignore
            await self._asgi_send(
                send=send, status_code=400, body={"error": "invalid content-type"}
            )
            return

        # read the entire payload
        raw_contents = await _read_asgi_body(receive)

        try:
            contents = json.loads(raw_contents.decode())
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
            await self._asgi_send(
                send=send, status_code=400, body={"error": "empty or invalid payload"}
            )
            return

        try:
            env = Envelope.model_validate(contents)
        except ValidationError:
            await self._asgi_send(
                send=send,
                status_code=400,
                body={"error": "contents do not match envelope schema"},
            )
            return

        expects_response = headers.get(b"x-uagents-connection") == b"sync"  # type: ignore

        if expects_response:
            # Add a future that will be resolved once the query is answered
            self._queries[env.sender] = asyncio.Future()

        if not is_user_address(env.sender):  # verify signature if sent from agent
            try:
                env.verify()
            except Exception as err:
                self._logger.warning(f"Failed to verify envelope: {err}")
                await self._asgi_send(
                    send=send, status_code=400, body={"error": str(err)}
                )
                return

        if not dispatcher.contains(address=env.target):
            await self._asgi_send(
                send=send, status_code=400, body={"error": "unable to route envelope"}
            )
            return

        await dispatcher.dispatch_msg(
            sender=env.sender,
            destination=env.target,
            schema_digest=env.schema_digest,
            message=env.decode_payload(),
            session=env.session,
        )

        # wait for any queries to be resolved
        if expects_response:
            timeout = (
                env.expires - datetime.now(timezone.utc).timestamp()
                if env.expires
                else DEFAULT_ENVELOPE_TIMEOUT_SECONDS
            )
            try:
                response_msg, schema_digest = await asyncio.wait_for(
                    self._queries[env.sender],
                    timeout,
                )
            except asyncio.TimeoutError:
                response_msg = ErrorMessage(
                    error="Query envelope expired"
                ).model_dump_json()
                schema_digest = ERROR_MESSAGE_DIGEST
            sender = env.target
            target = env.sender
            response = enclose_response_raw(
                json_message=response_msg,
                schema_digest=schema_digest,
                sender=sender,
                session=env.session,
                target=target,
            )
        else:
            response = "{}"

        await self._asgi_send(send=send, body=json.loads(response))
