"""Hostile boundary tests for the optional x402 buyer adapter."""

import gzip
from dataclasses import dataclass
from types import SimpleNamespace

import httpx
import pytest

pytest.importorskip("x402")

from x402.http.utils import (  # noqa: E402
    encode_payment_required_header,
    encode_payment_response_header,
)
from x402.schemas import (  # noqa: E402  # noqa: E402
    PaymentPayload,
    PaymentRequired,
    PaymentRequirements,
    SettleResponse,
)
from x402.schemas.hooks import RecoveredResponseResult  # noqa: E402

from uagents_adapter.x402 import (  # noqa: E402
    X402Buyer,
    X402ContentEncodingError,
    X402OutputValidationError,
    X402PurchaseError,
    X402PurchasePolicy,
    X402PurchaseRequest,
    X402PurchaseResult,
    X402ResponseTooLargeError,
    X402SettlementEvidenceError,
)


@dataclass
class FakeConfig:
    schemes: list
    policies: list | None = None
    spend_controls: dict | None = None
    payment_requirements_selector: object | None = None


def policy(**overrides):
    values = {
        "allowed_origins": frozenset({"https://seller.example"}),
        "max_amount_per_payment": "$0.01",
    }
    values.update(overrides)
    return X402PurchasePolicy(**values)


def test_policy_rejects_unlisted_origin_before_transport():
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(ValueError, match="not allowed"):
        buyer._validate_request(X402PurchaseRequest("GET", "https://evil.example/x"))


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
def test_policy_rejects_state_changing_method_by_default(method):
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(ValueError, match="not allowed"):
        buyer._validate_request(
            X402PurchaseRequest(method, "https://seller.example/product")
        )


@pytest.mark.parametrize(
    "header",
    ["PAYMENT-SIGNATURE", "Payment-Response", "X-PAYMENT", "Host"],
)
def test_caller_cannot_inject_payment_or_host_headers(header):
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(ValueError, match="reserved header"):
        buyer._validate_request(
            X402PurchaseRequest(
                "GET",
                "https://seller.example/product",
                headers={header: "attacker-controlled"},
            )
        )


def test_policy_rejects_insecure_http_by_default():
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(ValueError, match="insecure HTTP"):
        buyer._validate_request(X402PurchaseRequest("GET", "http://seller.example/x"))


def test_state_changing_method_requires_idempotency_key_when_enabled():
    buyer = X402Buyer(
        FakeConfig(schemes=[]), policy(allowed_methods=frozenset({"POST"}))
    )
    request = X402PurchaseRequest(
        "POST", "https://seller.example/product", content=b"{}"
    )
    with pytest.raises(ValueError, match="Idempotency-Key"):
        buyer._validate_request(request)
    method, _, _ = buyer._validate_request(
        X402PurchaseRequest(
            "POST",
            "https://seller.example/product",
            headers={"Idempotency-Key": "purchase-123"},
            content=b"{}",
        )
    )
    assert method == "POST"


@pytest.mark.parametrize(
    "headers",
    [
        {"Idempotency-Key": ""},
        {"Idempotency-Key": "   "},
        {"Idempotency-Key": "a", "idempotency-key": "b"},
    ],
)
def test_state_changing_method_rejects_empty_or_conflicting_idempotency_keys(
    headers,
):
    buyer = X402Buyer(
        FakeConfig(schemes=[]), policy(allowed_methods=frozenset({"POST"}))
    )
    with pytest.raises(ValueError, match="exactly one nonblank"):
        buyer._validate_request(
            X402PurchaseRequest(
                "POST",
                "https://seller.example/product",
                headers=headers,
                content=b"{}",
            )
        )


def test_state_changing_method_rejects_oversize_idempotency_key():
    buyer = X402Buyer(
        FakeConfig(schemes=[]), policy(allowed_methods=frozenset({"POST"}))
    )
    with pytest.raises(ValueError, match="255 UTF-8 bytes"):
        buyer._validate_request(
            X402PurchaseRequest(
                "POST",
                "https://seller.example/product",
                headers={"Idempotency-Key": "x" * 256},
                content=b"{}",
            )
        )


def test_allowed_origin_must_not_contain_path():
    buyer = X402Buyer(
        FakeConfig(schemes=[]),
        policy(allowed_origins=frozenset({"https://seller.example/path"})),
    )
    with pytest.raises(ValueError, match="must not include"):
        buyer._validate_request(
            X402PurchaseRequest("GET", "https://seller.example/product")
        )


def test_target_query_and_ipv6_origin_are_normalized():
    buyer = X402Buyer(
        FakeConfig(schemes=[]),
        policy(allowed_origins=frozenset({"https://[::1]:8443"})),
    )
    _, url, _ = buyer._validate_request(
        X402PurchaseRequest("GET", "https://[::1]:8443/product?city=London")
    )
    assert url.endswith("?city=London")


def test_spend_controls_override_caller_config():
    source = FakeConfig(schemes=[], spend_controls=False)
    buyer = X402Buyer(source, policy())
    assert buyer._config.spend_controls == {"max_amount_per_payment": "$0.01"}


def test_post_cap_policy_is_rejected():
    source = FakeConfig(schemes=[], policies=[lambda _version, values: values])
    with pytest.raises(ValueError, match="policies are not allowed"):
        X402Buyer(source, policy())


def test_post_cap_selector_is_rejected():
    source = FakeConfig(
        schemes=[], payment_requirements_selector=lambda _version, values: values[0]
    )
    with pytest.raises(ValueError, match="selectors are not allowed"):
        X402Buyer(source, policy())


@pytest.mark.asyncio
async def test_free_delivery_passes_buyer_validator(monkeypatch):
    async def handler(request):
        return httpx.Response(
            200,
            json={"ok": True},
            request=request,
        )

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: FakeClient(),
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    result = await buyer.purchase(
        X402PurchaseRequest("GET", "https://seller.example/product"),
        validate_output=lambda item: item.json() == {"ok": True},
    )
    assert result.payment_attempted is False
    assert result.reported_settlement is None


@pytest.mark.asyncio
async def test_output_rejection_preserves_delivery(monkeypatch):
    async def handler(request):
        return httpx.Response(200, content=b"{}", request=request)

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: FakeClient(),
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(X402OutputValidationError) as caught:
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: False,
        )
    assert caught.value.result.content == b"{}"


@pytest.mark.asyncio
async def test_response_cap_fails_with_bounded_evidence(monkeypatch):
    async def handler(request):
        return httpx.Response(200, content=b"abcdef", request=request)

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: FakeClient(),
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy(max_response_bytes=4))
    with pytest.raises(X402ResponseTooLargeError) as caught:
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: True,
        )
    assert caught.value.result.content == b"abcd"


@pytest.mark.asyncio
async def test_payment_attempt_without_receipt_fails_closed(monkeypatch):
    fake_client = FakeClient()
    selected = requirements()
    payment_required = PaymentRequired(x402_version=2, accepts=[selected])

    async def handler(request):
        fake_client.before_hook(
            SimpleNamespace(
                payment_required=payment_required,
                selected_requirements=selected,
            )
        )
        return httpx.Response(200, content=b'{"ok":true}', request=request)

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: fake_client,
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(X402SettlementEvidenceError) as caught:
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: True,
        )
    assert caught.value.result.payment_attempted is True


@pytest.mark.asyncio
async def test_official_transport_paid_path_binds_terms_and_receipt(monkeypatch):
    selected = requirements()
    payment_required = PaymentRequired(x402_version=2, accepts=[selected])
    fake_client = PayingFakeClient(selected)
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                402,
                headers={
                    "PAYMENT-REQUIRED": encode_payment_required_header(payment_required)
                },
                request=request,
            )
        assert "PAYMENT-SIGNATURE" in request.headers
        settlement = SettleResponse(
            success=True,
            transaction="0xabc",
            network=selected.network,
            amount=selected.amount,
        )
        return httpx.Response(
            200,
            content=b'{"forecast":"sunny"}',
            headers={"PAYMENT-RESPONSE": encode_payment_response_header(settlement)},
            request=request,
        )

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: fake_client,
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    result = await buyer.purchase(
        X402PurchaseRequest("GET", "https://seller.example/product"),
        validate_output=lambda item: item.json()["forecast"] == "sunny",
    )
    assert calls == 2
    assert result.payment_attempt_count == 1
    assert result.accepted_payment == selected
    assert result.reported_settlement.transaction == "0xabc"


@pytest.mark.asyncio
async def test_initial_402_body_is_bounded_before_sdk_buffering(monkeypatch):
    selected = requirements()
    payment_required = PaymentRequired(x402_version=2, accepts=[selected])
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(
            402,
            content=b"x" * 2_097_152,
            headers={
                "PAYMENT-REQUIRED": encode_payment_required_header(payment_required)
            },
            request=request,
        )

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: PayingFakeClient(selected),
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy(max_response_bytes=4))
    with pytest.raises(X402ResponseTooLargeError) as caught:
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: True,
        )
    assert calls == 1
    assert caught.value.result is None
    assert caught.value.payment_attempt.payment_attempt_count == 0


@pytest.mark.asyncio
async def test_compressed_initial_402_is_rejected_before_sdk_buffering(monkeypatch):
    selected = requirements()
    payment_required = PaymentRequired(x402_version=2, accepts=[selected])
    inflated = b"x" * 2_097_152
    encoded = gzip.compress(inflated)
    assert len(encoded) < 4096

    async def handler(request):
        return httpx.Response(
            402,
            content=encoded,
            headers={
                "Content-Encoding": "gzip",
                "PAYMENT-REQUIRED": encode_payment_required_header(payment_required),
            },
            request=request,
        )

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: PayingFakeClient(selected),
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy(max_response_bytes=4096))
    with pytest.raises(X402ContentEncodingError, match="identity encoding") as caught:
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: True,
        )
    assert caught.value.payment_attempt.payment_attempt_count == 0


@pytest.mark.asyncio
async def test_compressed_free_delivery_is_rejected(monkeypatch):
    async def handler(request):
        return httpx.Response(
            200,
            content=gzip.compress(b'{"ok":true}'),
            headers={"Content-Encoding": "gzip"},
            request=request,
        )

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: FakeClient(),
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(X402ContentEncodingError, match="identity encoding"):
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: True,
        )


@pytest.mark.asyncio
async def test_post_signature_timeout_preserves_possible_spend_evidence(monkeypatch):
    selected = requirements()
    payment_required = PaymentRequired(x402_version=2, accepts=[selected])
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                402,
                headers={
                    "PAYMENT-REQUIRED": encode_payment_required_header(payment_required)
                },
                request=request,
            )
        assert "PAYMENT-SIGNATURE" in request.headers
        raise httpx.ReadTimeout("seller timed out after payment send", request=request)

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: PayingFakeClient(selected),
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(X402PurchaseError) as caught:
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: True,
        )
    assert calls == 2
    assert caught.value.result is None
    assert caught.value.payment_attempt.payment_attempt_count == 1
    assert caught.value.payment_attempt.accepted_payment == selected


@pytest.mark.asyncio
async def test_selected_payment_must_be_in_original_challenge(monkeypatch):
    offered = requirements()
    selected = PaymentRequirements(
        scheme=offered.scheme,
        network=offered.network,
        asset=offered.asset,
        amount="100000000",
        pay_to=offered.pay_to,
        max_timeout_seconds=offered.max_timeout_seconds,
    )
    payment_required = PaymentRequired(x402_version=2, accepts=[offered])

    async def handler(request):
        return httpx.Response(
            402,
            headers={
                "PAYMENT-REQUIRED": encode_payment_required_header(payment_required)
            },
            request=request,
        )

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: PayingFakeClient(selected),
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(X402PurchaseError, match="selected_payment_not_offered"):
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: True,
        )


@pytest.mark.asyncio
async def test_transport_recovery_cannot_create_second_payment(monkeypatch):
    selected = requirements()
    payment_required = PaymentRequired(x402_version=2, accepts=[selected])
    fake_client = RecoveringPayingFakeClient(selected)
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                402,
                headers={
                    "PAYMENT-REQUIRED": encode_payment_required_header(payment_required)
                },
                request=request,
            )
        settlement = SettleResponse(
            success=True,
            transaction="0xabc",
            network=selected.network,
            amount=selected.amount,
        )
        return httpx.Response(
            200,
            content=b"{}",
            headers={"PAYMENT-RESPONSE": encode_payment_response_header(settlement)},
            request=request,
        )

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer.x402Client.from_config",
        lambda _config: fake_client,
    )
    buyer = X402Buyer(FakeConfig(schemes=[]), policy())
    with pytest.raises(X402PurchaseError, match="multiple_payment_attempts_denied"):
        await buyer.purchase(
            X402PurchaseRequest("GET", "https://seller.example/product"),
            validate_output=lambda _item: True,
        )
    assert calls == 2


def test_foreign_settlement_terms_are_not_promoted():
    selected = requirements()
    result = X402PurchaseResult(
        status_code=200,
        headers={},
        content=b"{}",
        payment_attempted=True,
        payment_attempt_count=1,
        accepted_payment=selected,
        reported_settlement=SettleResponse(
            success=True,
            transaction="0xabc",
            network="eip155:84532",
            amount=selected.amount,
        ),
    )
    with pytest.raises(X402SettlementEvidenceError, match="network"):
        X402Buyer._validate_settlement(result)


def requirements():
    return PaymentRequirements(
        scheme="exact",
        network="eip155:8453",
        asset="0x0000000000000000000000000000000000000000",
        amount="10000",
        pay_to="0x1234567890123456789012345678901234567890",
        max_timeout_seconds=300,
    )


def install_transport(monkeypatch, handler):
    monkeypatch.setattr(
        "uagents_adapter.x402.buyer._make_underlying_transport",
        lambda: httpx.MockTransport(handler),
    )


class FakeClient:
    def __init__(self):
        self.before_hook = None

    def on_before_payment_creation(self, hook):
        self.before_hook = hook
        return self


class PayingFakeClient(FakeClient):
    def __init__(self, selected):
        super().__init__()
        self.selected = selected

    async def create_payment_payload(self, payment_required):
        verdict = self.before_hook(
            SimpleNamespace(
                payment_required=payment_required,
                selected_requirements=self.selected,
            )
        )
        if verdict is not None:
            raise RuntimeError(verdict.reason)
        return PaymentPayload(
            x402_version=2,
            payload={"signature": "0xmock"},
            accepted=self.selected,
        )

    async def handle_payment_response(self, _context):
        return None


class RecoveringPayingFakeClient(PayingFakeClient):
    async def handle_payment_response(self, _context):
        return RecoveredResponseResult()
