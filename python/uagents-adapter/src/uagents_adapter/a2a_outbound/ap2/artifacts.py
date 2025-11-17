"""Formal AP2 types from their GitHub repo"""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional

# Use pydantic.v1 to avoid mixing v2 models with uAgents' v1-based Model classes
from pydantic.v1 import BaseModel, Field

# ---------------------- PAYMENT REQUEST/RESPONSE MODELS ---------------------- #


class PaymentCurrencyAmount(BaseModel):
    currency: str = Field(..., description="ISO 4217 currency code")
    value: float = Field(..., description="Monetary value in major units")


class PaymentItem(BaseModel):
    label: str
    amount: PaymentCurrencyAmount
    pending: Optional[bool] = None
    refund_period: int = Field(
        default=30, description="Refund duration in days (spec: refund_period)"
    )


class PaymentMethodData(BaseModel):
    supported_methods: str = Field(..., description="Identifier for the payment method")
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Method specific parameters / processor hints"
    )


class PaymentDetailsInit(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for this payment details instance (transaction/cart id)",
    )
    display_items: List[PaymentItem]
    total: PaymentItem
    shipping_options: Optional[str] = None  # Simplified placeholder
    modifiers: Optional[List[Dict[str, Any]]] = None


class PaymentOptions(BaseModel):
    request_payer_name: bool = False
    request_payer_email: bool = False
    request_payer_phone: bool = False
    request_shipping: bool = True
    shipping_type: Optional[str] = None


class PaymentRequest(BaseModel):
    method_data: List[PaymentMethodData]
    details: PaymentDetailsInit
    options: Optional[PaymentOptions] = None
    # Shipping address omitted for now; can be added when needed.


class PaymentResponse(BaseModel):
    request_id: str
    method_name: str
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Opaque method-specific response payload (e.g. token id)",
    )


# ---------------------- MANDATE MODELS ---------------------- #


class CartContents(BaseModel):
    id: str
    payment_request: PaymentRequest
    user_cart_confirmation_required: bool = True
    cart_expiry: str = Field(..., description="ISO 8601 expiry timestamp")
    merchant_name: str


class CartMandate(BaseModel):
    contents: CartContents
    merchant_authorization: Optional[str] = Field(
        None, description="Placeholder merchant signature / JWT"
    )
    cart_hash: Optional[str] = Field(
        None,
        description="Integrity hash over canonicalized CartContents (must be computed explicitly)",
    )


class PaymentMandateContents(BaseModel):
    payment_mandate_id: str
    payment_details_id: str
    payment_details_total: PaymentItem
    payment_response: PaymentResponse
    merchant_agent: str
    modality: Literal["human_present", "human_not_present"] = "human_present"
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z"
    )


class PaymentMandate(BaseModel):
    payment_mandate_contents: PaymentMandateContents
    user_authorization: Optional[str] = Field(
        None, description="Placeholder user signature / VP over hashes"
    )
    payment_mandate_hash: Optional[str] = Field(
        None,
        description=(
            "Integrity hash over canonicalized PaymentMandateContents (must be computed"
            " explicitly)"
        ),
    )


# ---------------------- ACCEPT/DENY MODELS ---------------------- #


class DenyCartMandate(BaseModel):
    reason: Optional[str] = None


class PaymentSuccess(BaseModel):
    transaction_id: str


class PaymentFailure(BaseModel):
    transaction_id: str
    reason: Optional[str] = None


# ---------------------- HASH / UTILS ---------------------- #


def compute_canonical_hash(obj: Dict[str, Any]) -> str:
    """Return SHA-256 over canonical JSON (sorted keys, compact separators)."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Convenience builders (minimal now, can expand later)


def build_basic_payment_request(
    *,
    amount: float,
    currency: str,
    description: str,
    supported_method: str,
    request_id: str,
) -> PaymentRequest:
    item = PaymentItem(
        label=description,
        amount=PaymentCurrencyAmount(currency=currency, value=amount),
    )
    total = PaymentItem(
        label="Total", amount=PaymentCurrencyAmount(currency=currency, value=amount)
    )
    return PaymentRequest(
        method_data=[PaymentMethodData(supported_methods=supported_method, data={})],
        details=PaymentDetailsInit(id=request_id, display_items=[item], total=total),
        options=PaymentOptions(request_shipping=False),
    )


def compute_cart_hash(cart: CartContents) -> str:
    return compute_canonical_hash(cart.dict())


def compute_payment_mandate_hash(contents: PaymentMandateContents) -> str:
    return compute_canonical_hash(contents.dict())


__all__ = [
    "PaymentCurrencyAmount",
    "PaymentItem",
    "PaymentMethodData",
    "PaymentDetailsInit",
    "PaymentOptions",
    "PaymentRequest",
    "PaymentResponse",
    "CartContents",
    "CartMandate",
    "PaymentMandateContents",
    "PaymentMandate",
    "DenyCartMandate",
    "PaymentSuccess",
    "PaymentFailure",
    "compute_canonical_hash",
    "build_basic_payment_request",
    "compute_cart_hash",
    "compute_payment_mandate_hash",
]
