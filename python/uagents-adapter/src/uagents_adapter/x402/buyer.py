"""Buyer-owned delivery boundary around the official x402 HTTP client.

This module deliberately does not expose a generic uAgent message handler. The
calling application constructs the request, supplies the wallet-backed x402
scheme configuration, and owns the output validator. That keeps untrusted
agent messages from selecting arbitrary URLs, methods, headers, or spend.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any
from urllib.parse import urlsplit

import httpx
from x402 import SpendControlAsset, x402Client, x402ClientConfig
from x402.http.clients import x402_httpx_transport
from x402.http.clients.httpx import PaymentError
from x402.http.constants import PAYMENT_RESPONSE_HEADER, X_PAYMENT_RESPONSE_HEADER
from x402.http.utils import decode_payment_response_header
from x402.schemas import PaymentRequirements, PaymentRequirementsV1, SettleResponse
from x402.schemas.hooks import AbortResult

_PAYMENT_HEADERS = frozenset(
    {
        "payment-signature",
        "payment-required",
        "payment-response",
        "x-payment",
        "x-payment-required",
        "x-payment-response",
    }
)
_MAX_IDEMPOTENCY_KEY_BYTES = 255


class _ResponseLimitExceededError(PaymentError):
    """Internal signal raised before an x402 transport can over-buffer a body."""

    def __init__(self, limit: int) -> None:
        super().__init__(f"response exceeded {limit} bytes")
        self.limit = limit


class _UnsupportedContentEncodingError(PaymentError):
    """Internal signal for encoded bodies that could inflate past the cap."""

    def __init__(self, encoding: str) -> None:
        super().__init__(
            f"response Content-Encoding {encoding!r} is not supported; "
            "bounded x402 responses require identity encoding"
        )
        self.encoding = encoding


class _BoundedResponseStream(httpx.AsyncByteStream):
    """Limit every response stream below the x402 buffering layer."""

    def __init__(self, stream: httpx.AsyncByteStream, limit: int) -> None:
        self._stream = stream
        self._limit = limit
        self._seen = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self._stream:
            remaining = self._limit - self._seen
            if len(chunk) <= remaining:
                self._seen += len(chunk)
                yield chunk
                continue
            if remaining > 0:
                self._seen += remaining
                yield chunk[:remaining]
            await self._stream.aclose()
            raise _ResponseLimitExceededError(self._limit)

    async def aclose(self) -> None:
        await self._stream.aclose()


class _BoundedTransport(httpx.AsyncBaseTransport):
    """Wrap the raw HTTP transport so initial 402 and retry bodies are bounded."""

    def __init__(self, transport: httpx.AsyncBaseTransport, limit: int) -> None:
        self._transport = transport
        self._limit = limit

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self._transport.handle_async_request(request)
        encoding = response.headers.get("content-encoding", "").strip().lower()
        if encoding and encoding != "identity":
            await response.aclose()
            raise _UnsupportedContentEncodingError(encoding)
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            stream=_BoundedResponseStream(response.stream, self._limit),
            extensions=response.extensions,
        )

    async def aclose(self) -> None:
        await self._transport.aclose()


def _make_underlying_transport() -> httpx.AsyncBaseTransport:
    return httpx.AsyncHTTPTransport()


@dataclass(frozen=True)
class X402PurchaseRequest:
    """An application-owned HTTP request that may be paid once."""

    method: str
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    content: bytes | None = None


@dataclass(frozen=True)
class X402PurchasePolicy:
    """Fail-closed transport and spend bounds for one buyer."""

    allowed_origins: frozenset[str]
    max_amount_per_payment: str
    allowed_methods: frozenset[str] = frozenset({"GET"})
    allowed_assets: tuple[SpendControlAsset, ...] = ()
    max_response_bytes: int = 1_000_000
    timeout_seconds: float = 30.0
    allow_insecure_http: bool = False

    def __post_init__(self) -> None:
        if not self.allowed_origins:
            raise ValueError("allowed_origins must not be empty")
        if not self.max_amount_per_payment:
            raise ValueError("max_amount_per_payment must not be empty")
        if self.max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class X402PurchaseResult:
    """Delivery bytes plus native, unpromoted settlement evidence."""

    status_code: int
    headers: Mapping[str, str]
    content: bytes
    payment_attempted: bool
    payment_attempt_count: int
    accepted_payment: PaymentRequirements | PaymentRequirementsV1 | None
    reported_settlement: SettleResponse | None

    def json(self) -> Any:
        """Decode the bounded delivery body as JSON."""
        return json.loads(self.content)


@dataclass(frozen=True)
class X402PaymentAttempt:
    """Native possible-spend evidence retained when no response was delivered."""

    payment_attempt_count: int
    accepted_payment: PaymentRequirements | PaymentRequirementsV1 | None

    @property
    def payment_attempted(self) -> bool:
        return self.payment_attempt_count > 0


OutputValidator = Callable[[X402PurchaseResult], bool | None | Awaitable[bool | None]]


class X402PurchaseError(RuntimeError):
    """Base error that preserves any delivery and settlement evidence."""

    def __init__(
        self,
        message: str,
        result: X402PurchaseResult | None = None,
        payment_attempt: X402PaymentAttempt | None = None,
    ) -> None:
        super().__init__(message)
        self.result = result
        if payment_attempt is None and result is not None:
            payment_attempt = X402PaymentAttempt(
                payment_attempt_count=result.payment_attempt_count,
                accepted_payment=result.accepted_payment,
            )
        self.payment_attempt = payment_attempt


class X402ResponseTooLargeError(X402PurchaseError):
    """The response exceeded the caller's byte budget."""


class X402ContentEncodingError(X402PurchaseError):
    """The response used an encoding that could inflate past the byte budget."""


class X402SettlementEvidenceError(X402PurchaseError):
    """A payment was created but valid success evidence was not returned."""


class X402DeliveryError(X402PurchaseError):
    """The seller did not return a successful application response."""


class X402OutputValidationError(X402PurchaseError):
    """The paid or free delivery failed the buyer-owned output contract."""


class X402Buyer:
    """Execute bounded x402 HTTP purchases using the official SDK transport."""

    def __init__(self, config: x402ClientConfig, policy: X402PurchasePolicy) -> None:
        self._policy = policy
        if config.policies:
            raise ValueError(
                "caller-provided x402 policies are not allowed because they run "
                "after spend controls"
            )
        if config.payment_requirements_selector is not None:
            raise ValueError(
                "caller-provided payment requirement selectors are not allowed "
                "because they run after spend controls"
            )
        spend_controls: dict[str, Any] = {
            "max_amount_per_payment": policy.max_amount_per_payment,
        }
        if policy.allowed_assets:
            spend_controls["allowed_assets"] = list(policy.allowed_assets)
        self._config = replace(
            config,
            policies=None,
            payment_requirements_selector=None,
            spend_controls=spend_controls,
        )

    async def purchase(
        self,
        request: X402PurchaseRequest,
        *,
        validate_output: OutputValidator,
    ) -> X402PurchaseResult:
        """Execute one logical purchase and return only validated delivery."""
        method, url, headers = self._validate_request(request)
        payment_attempt_count = 0
        accepted_payment: PaymentRequirements | PaymentRequirementsV1 | None = None
        client = x402Client.from_config(self._config)

        def admit_one_payment(context: Any) -> AbortResult | None:
            nonlocal accepted_payment, payment_attempt_count
            if not any(
                context.selected_requirements == offered
                for offered in context.payment_required.accepts
            ):
                return AbortResult(
                    reason="selected_payment_not_offered",
                    message=(
                        "selected payment terms must exactly match the seller's "
                        "original challenge"
                    ),
                )
            if payment_attempt_count >= 1:
                return AbortResult(
                    reason="multiple_payment_attempts_denied",
                    message="X402Buyer permits one payment creation per purchase",
                )
            payment_attempt_count += 1
            accepted_payment = context.selected_requirements
            return None

        client.on_before_payment_creation(admit_one_payment)
        raw_transport = _BoundedTransport(
            _make_underlying_transport(),
            self._policy.max_response_bytes,
        )
        transport = x402_httpx_transport(client, raw_transport)
        timeout = httpx.Timeout(self._policy.timeout_seconds)

        try:
            async with httpx.AsyncClient(
                transport=transport,
                timeout=timeout,
                follow_redirects=False,
            ) as http:
                built = http.build_request(
                    method,
                    url,
                    headers=headers,
                    content=request.content,
                )
                response = await http.send(built, stream=True)
                try:
                    content, overflow = await self._read_bounded(response)
                    result = self._make_result(
                        response,
                        content,
                        payment_attempt_count,
                        accepted_payment,
                    )
                finally:
                    await response.aclose()
        except X402PurchaseError:
            raise
        except _ResponseLimitExceededError as exc:
            raise X402ResponseTooLargeError(
                str(exc),
                payment_attempt=X402PaymentAttempt(
                    payment_attempt_count=payment_attempt_count,
                    accepted_payment=accepted_payment,
                ),
            ) from exc
        except _UnsupportedContentEncodingError as exc:
            raise X402ContentEncodingError(
                str(exc),
                payment_attempt=X402PaymentAttempt(
                    payment_attempt_count=payment_attempt_count,
                    accepted_payment=accepted_payment,
                ),
            ) from exc
        except Exception as exc:
            raise X402PurchaseError(
                f"x402 purchase failed: {exc}",
                payment_attempt=X402PaymentAttempt(
                    payment_attempt_count=payment_attempt_count,
                    accepted_payment=accepted_payment,
                ),
            ) from exc

        if overflow:
            raise X402ResponseTooLargeError(
                f"response exceeded {self._policy.max_response_bytes} bytes",
                result,
            )
        self._validate_settlement(result)
        if not 200 <= result.status_code < 300:
            raise X402DeliveryError(
                f"seller returned HTTP {result.status_code}",
                result,
            )
        await self._run_output_validator(validate_output, result)
        return result

    def _validate_request(
        self, request: X402PurchaseRequest
    ) -> tuple[str, str, dict[str, str]]:
        method = request.method.upper().strip()
        allowed_methods = {item.upper() for item in self._policy.allowed_methods}
        if not allowed_methods:
            raise ValueError("allowed_methods must not be empty")
        if method not in allowed_methods:
            raise ValueError(f"HTTP method {method!r} is not allowed")

        parsed = urlsplit(request.url)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ValueError("url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password or parsed.fragment:
            raise ValueError("url credentials and fragments are not allowed")
        if parsed.scheme == "http" and not self._policy.allow_insecure_http:
            raise ValueError("insecure HTTP is not allowed")

        origin = self._origin(parsed, require_origin_only=False)
        allowed_origins = {
            self._origin(urlsplit(item), require_origin_only=True)
            for item in self._policy.allowed_origins
        }
        if origin not in allowed_origins:
            raise ValueError(f"origin {origin!r} is not allowed")

        headers: dict[str, str] = {}
        for name, value in request.headers.items():
            lowered = name.lower().strip()
            if lowered in _PAYMENT_HEADERS or lowered in {"host", "content-length"}:
                raise ValueError(f"caller may not set reserved header {name!r}")
            if "\r" in name or "\n" in name or "\r" in value or "\n" in value:
                raise ValueError("header names and values must not contain newlines")
            headers[name] = value
        if method in {"GET", "HEAD"} and request.content is not None:
            raise ValueError(f"HTTP method {method!r} must not include a request body")
        if method not in {"GET", "HEAD", "OPTIONS"}:
            idempotency_keys = [
                value.strip()
                for name, value in headers.items()
                if name.strip().lower() == "idempotency-key"
            ]
            if len(idempotency_keys) != 1 or not idempotency_keys[0]:
                raise ValueError(
                    "replayed state-changing methods require exactly one nonblank "
                    "Idempotency-Key"
                )
            if len(idempotency_keys[0].encode("utf-8")) > _MAX_IDEMPOTENCY_KEY_BYTES:
                raise ValueError(
                    f"Idempotency-Key must not exceed "
                    f"{_MAX_IDEMPOTENCY_KEY_BYTES} UTF-8 bytes"
                )
        return method, request.url, headers

    @staticmethod
    def _origin(parsed: Any, *, require_origin_only: bool) -> str:
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ValueError("allowed origins must be absolute HTTP(S) origins")
        if (
            parsed.username
            or parsed.password
            or (require_origin_only and (parsed.path not in {"", "/"} or parsed.query))
            or parsed.fragment
        ):
            raise ValueError(
                "allowed origins must not include credentials, path, query, or fragment"
            )
        default_port = 443 if parsed.scheme == "https" else 80
        port = parsed.port or default_port
        suffix = "" if port == default_port else f":{port}"
        host = parsed.hostname.lower()
        if ":" in host:
            host = f"[{host}]"
        return f"{parsed.scheme}://{host}{suffix}"

    async def _read_bounded(self, response: httpx.Response) -> tuple[bytes, bool]:
        limit = self._policy.max_response_bytes
        body = bytearray()
        try:
            async for chunk in response.aiter_bytes():
                remaining = limit - len(body)
                if len(chunk) > remaining:
                    if remaining > 0:
                        body.extend(chunk[:remaining])
                    return bytes(body), True
                body.extend(chunk)
        except _ResponseLimitExceededError:
            return bytes(body), True
        return bytes(body), False

    @staticmethod
    def _make_result(
        response: httpx.Response,
        content: bytes,
        payment_attempt_count: int,
        accepted_payment: PaymentRequirements | PaymentRequirementsV1 | None,
    ) -> X402PurchaseResult:
        reported_settlement = None
        raw_settlement = response.headers.get(PAYMENT_RESPONSE_HEADER)
        if raw_settlement is None:
            raw_settlement = response.headers.get(X_PAYMENT_RESPONSE_HEADER)
        if raw_settlement:
            try:
                reported_settlement = decode_payment_response_header(raw_settlement)
            except Exception as exc:
                partial = X402PurchaseResult(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=content,
                    payment_attempted=payment_attempt_count > 0,
                    payment_attempt_count=payment_attempt_count,
                    accepted_payment=accepted_payment,
                    reported_settlement=None,
                )
                raise X402SettlementEvidenceError(
                    f"invalid payment response header: {exc}", partial
                ) from exc
        return X402PurchaseResult(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=content,
            payment_attempted=payment_attempt_count > 0,
            payment_attempt_count=payment_attempt_count,
            accepted_payment=accepted_payment,
            reported_settlement=reported_settlement,
        )

    @staticmethod
    def _validate_settlement(result: X402PurchaseResult) -> None:
        if not result.payment_attempted:
            if result.reported_settlement is not None:
                raise X402SettlementEvidenceError(
                    "seller reported settlement without a buyer payment attempt",
                    result,
                )
            return
        settlement = result.reported_settlement
        accepted = result.accepted_payment
        if accepted is None:
            raise X402SettlementEvidenceError(
                "payment attempt is missing the selected payment requirements",
                result,
            )
        if settlement is None:
            raise X402SettlementEvidenceError(
                "payment was attempted but settlement evidence is missing",
                result,
            )
        if not settlement.success:
            raise X402SettlementEvidenceError(
                settlement.error_message
                or settlement.error_reason
                or "settlement failed",
                result,
            )
        if settlement.network != accepted.network:
            raise X402SettlementEvidenceError(
                "reported settlement network does not match accepted payment terms",
                result,
            )
        if settlement.amount is not None and settlement.amount != accepted.get_amount():
            raise X402SettlementEvidenceError(
                "reported settlement amount does not match accepted payment terms",
                result,
            )
        if not settlement.transaction:
            raise X402SettlementEvidenceError(
                "reported settlement transaction is empty",
                result,
            )

    @staticmethod
    async def _run_output_validator(
        validator: OutputValidator, result: X402PurchaseResult
    ) -> None:
        try:
            verdict = validator(result)
            if inspect.isawaitable(verdict):
                verdict = await verdict
        except Exception as exc:
            raise X402OutputValidationError(
                f"output validation raised: {exc}", result
            ) from exc
        if verdict is False:
            raise X402OutputValidationError(
                "output validation rejected delivery", result
            )
