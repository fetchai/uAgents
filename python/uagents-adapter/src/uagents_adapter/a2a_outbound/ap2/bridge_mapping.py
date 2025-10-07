"""Bridge mapping utilities between Simple AP2 protocol and Fetch.ai payment protocol.

All conversions follow the naming pattern: source_to_target()
"""

from __future__ import annotations

import json
import re
import uuid

# (No direct need to import message envelopes here; mapping uses mandate objects only)
from datetime import datetime, timedelta, timezone
from typing import Any, Union

# A2A SDK imports
from a2a.types import DataPart, Message, Part, Role

from .artifacts import (
    CartContents,
    CartMandate,
    DenyCartMandate,
    PaymentCurrencyAmount,
    PaymentFailure,
    PaymentItem,
    PaymentMandate,
    PaymentMandateContents,
    PaymentRequest,
    PaymentResponse,
    PaymentSuccess,
    build_basic_payment_request,
    compute_cart_hash,
    compute_payment_mandate_hash,
)
from .fetchai_payment_protocol import (
    CancelPayment,
    CommitPayment,
    CompletePayment,
    Funds,
    RejectPayment,
    RequestPayment,
)

# ===================== A2A DATA KEYS =====================

# AP2 data keys for A2A DataParts
CART_MANDATE_KEY = "ap2.mandates.CartMandate"
PAYMENT_MANDATE_KEY = "ap2.mandates.PaymentMandate"
DENY_CART_MANDATE_KEY = "ap2.mandates.DenyCartMandate"
PAYMENT_SUCCESS_KEY = "ap2.mandates.PaymentSuccess"
PAYMENT_FAILURE_KEY = "ap2.mandates.PaymentFailure"


# ===================== UTILITY FUNCTIONS =====================


def pretty_print_model(model: Any, label: str) -> None:
    """Pretty print any Pydantic model or data structure with a descriptive label.

    Args:
        model: The data model to print (Pydantic model, dict, etc.)
        label: Descriptive label for the model
    """
    print(f"\n\n🔄 {label}")

    # Pretty print the model data
    try:
        if hasattr(model, "dict"):
            # Pydantic model
            model_dict = model.dict()
        elif hasattr(model, "__dict__"):
            # Regular class with attributes
            model_dict = model.__dict__
        elif isinstance(model, dict):
            # Already a dictionary
            model_dict = model
        else:
            # Convert to string representation
            print(f"   📄 Data: {model}")
            return

        # Format as pretty JSON
        formatted_json = json.dumps(model_dict, indent=2, default=str)
        # Shorten long ID field values for readability
        # by truncating the value with "..." using regex (only if longer than 12 chars)
        id_fields = [
            "transaction_id",
            "transaction_token",
            "request_id",
            "payment_mandate_id",
            "payment_mandate_hash",
            "cart_hash",
            "id",
        ]
        for field in id_fields:
            pattern = rf'"{field}": "(.{{6}}).{{1,}}(.{{6}})"'
            replacement = rf'"{field}": "\1...\2"'
            formatted_json = re.sub(pattern, replacement, formatted_json)
        # Indent each line for consistent formatting
        indented_lines = ["   | " + line for line in formatted_json.split("\n")]
        print("\n".join(indented_lines))

    except Exception as e:
        print(f"   ⚠️  Could not format model: {e}")
        print(f"   | Data: {model}")


# ===================== GENERIC A2A FUNCTIONS =====================


def extract_ap2_mandate_from_a2a(
    a2a_msg: Message, mandate_class
) -> Union[CartMandate, PaymentMandate]:
    """Extract AP2 mandate from A2A Message DataPart.

    Args:
        a2a_msg: A2A Message containing AP2 data
        mandate_class: Pydantic model class (CartMandate or PaymentMandate)

    Returns:
        Instance of the specified mandate class

    Raises:
        ValueError: If mandate data not found
    """
    # Determine data key from mandate class
    if mandate_class == CartMandate:
        data_key = CART_MANDATE_KEY
    elif mandate_class == PaymentMandate:
        data_key = PAYMENT_MANDATE_KEY
    else:
        raise ValueError(f"Unsupported mandate class: {mandate_class}")

    # Extract data from A2A message
    for part in a2a_msg.parts:
        has_data = hasattr(part.root, "data") and isinstance(part.root.data, dict)
        if has_data and data_key in part.root.data:
            return mandate_class(**part.root.data[data_key])

    raise ValueError(
        f"AP2 mandate data for {mandate_class.__name__} not found in A2A message"
    )


def wrap_ap2_mandate_in_a2a(
    mandate: Union[CartMandate, PaymentMandate],
    context_id: str | None = None,
    task_id: str | None = None,
) -> Message:
    """Wrap AP2 mandate in A2A Message format.

    Args:
        mandate: AP2 mandate instance (CartMandate or PaymentMandate)
        context_id: Optional A2A context ID
        task_id: Optional A2A task ID

    Returns:
        A2A Message containing the AP2 mandate data
    """
    # Determine data key from mandate type
    if isinstance(mandate, CartMandate):
        data_key = CART_MANDATE_KEY
    elif isinstance(mandate, PaymentMandate):
        data_key = PAYMENT_MANDATE_KEY
    else:
        raise ValueError(f"Unsupported mandate type: {type(mandate)}")

    # Create A2A message with AP2 data
    message = Message(
        message_id=uuid.uuid4().hex,
        parts=[Part(root=DataPart(data={data_key: mandate.dict()}))],
        role=Role.agent,
        context_id=context_id,
        task_id=task_id,
    )

    return message


# ===================== UTILITY FUNCTIONS =====================


def expiry_to_deadline_seconds(expiry_iso: str) -> int:
    """Convert an ISO 8601 expiry string (with optional trailing 'Z') to remaining seconds."""
    trimmed = expiry_iso.rstrip("Z")
    expiry_dt = datetime.fromisoformat(trimmed)
    if expiry_dt.tzinfo is None:
        expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = (expiry_dt - now).total_seconds()
    return int(delta)


# ===================== AP2 -> FETCH.AI CONVERSIONS =====================


def cartmandate_to_requestpayment(
    cart_mandate: CartMandate, recipient: str
) -> RequestPayment:
    """Convert AP2 CartMandate to Fetch.ai RequestPayment."""
    pretty_print_model(
        cart_mandate, "(INPUT: AP2 CartMandate) Converting to Fetch.ai RequestPayment"
    )

    total_item = cart_mandate.contents.payment_request.details.total
    amount = str(total_item.amount.value)
    currency = total_item.amount.currency

    # Find the supported payment method
    payment_method = cart_mandate.contents.payment_request.method_data[
        0
    ].supported_methods
    metadata = cart_mandate.contents.payment_request.method_data[0].data
    funds = Funds(amount=amount, currency=currency, payment_method=payment_method)

    derived_deadline = expiry_to_deadline_seconds(cart_mandate.contents.cart_expiry)

    # Use the payment request description or total label as description
    description = (
        total_item.label
        if total_item.label != "Total"
        else f"Cart from {cart_mandate.contents.merchant_name}"
    )

    # Add cart hash to metadata for integrity verification
    metadata["cart_hash"] = cart_mandate.cart_hash or ""

    request_payment = RequestPayment(
        accepted_funds=[funds],
        recipient=recipient,
        deadline_seconds=derived_deadline,
        reference=cart_mandate.contents.id,
        description=description,
        metadata=metadata,
    )

    pretty_print_model(request_payment, "(OUTPUT: Fetch.ai RequestPayment)")
    return request_payment


def paymentmandate_to_commitpayment(
    payment_mandate: PaymentMandate, recipient: str
) -> CommitPayment:
    """Convert AP2 PaymentMandate to Fetch.ai CommitPayment."""
    pretty_print_model(
        payment_mandate,
        "(INPUT: AP2 PaymentMandate) Converting to Fetch.ai CommitPayment",
    )

    total_item = payment_mandate.payment_mandate_contents.payment_details_total
    amount = str(total_item.amount.value)
    currency = total_item.amount.currency

    # Find the payment method from PaymentResponse
    payment_method = (
        payment_mandate.payment_mandate_contents.payment_response.method_name
    )
    funds = Funds(amount=amount, currency=currency, payment_method=payment_method)

    # Get transaction token from payment response details
    payment_details = payment_mandate.payment_mandate_contents.payment_response.details
    token = (
        payment_details.get("transaction_token")
        or payment_details.get("token")
        or "unknown_token"
    )

    # Use the payment details total label as description if it's more descriptive than "Total"
    description = (
        total_item.label
        if total_item.label != "Total"
        else "Commit corresponding to PaymentMandate"
    )

    commit_payment = CommitPayment(
        funds=funds,
        recipient=recipient,
        transaction_id=token,
        reference=payment_mandate.payment_mandate_contents.payment_details_id,
        description=description,
        metadata={
            "payment_mandate_hash": payment_mandate.payment_mandate_hash or "",
        },
    )

    pretty_print_model(commit_payment, "(OUTPUT: Fetch.ai CommitPayment)")
    return commit_payment


def denycartmandate_to_rejectpayment(
    deny_cart_mandate: DenyCartMandate,
) -> RejectPayment:
    """Convert AP2 DenyCartMandate to Fetch.ai RejectPayment."""
    pretty_print_model(
        deny_cart_mandate,
        "(INPUT: AP2 DenyCartMandate) Converting to Fetch.ai RejectPayment",
    )

    reject_payment = RejectPayment(reason=deny_cart_mandate.reason)

    pretty_print_model(reject_payment, "(OUTPUT: Fetch.ai RejectPayment)")
    return reject_payment


def paymentsuccess_to_completepayment(
    payment_success: PaymentSuccess,
) -> CompletePayment:
    """Convert AP2 PaymentSuccess to Fetch.ai CompletePayment."""
    pretty_print_model(
        payment_success,
        "(INPUT: AP2 PaymentSuccess) Converting to Fetch.ai CompletePayment",
    )

    complete_payment = CompletePayment(transaction_id=payment_success.transaction_id)

    pretty_print_model(complete_payment, "(OUTPUT: Fetch.ai CompletePayment)")
    return complete_payment


def paymentfailure_to_cancelpayment(payment_failure: PaymentFailure) -> CancelPayment:
    """Convert AP2 PaymentFailure to Fetch.ai CancelPayment."""
    pretty_print_model(
        payment_failure,
        "(INPUT: AP2 PaymentFailure) Converting to Fetch.ai CancelPayment",
    )

    cancel_payment = CancelPayment(
        transaction_id=payment_failure.transaction_id, reason=payment_failure.reason
    )

    pretty_print_model(cancel_payment, "(OUTPUT: Fetch.ai CancelPayment)")
    return cancel_payment


# ===================== FETCH.AI -> AP2 CONVERSIONS =====================


def requestpayment_to_cartmandate(
    request_payment: RequestPayment, merchant_name: str = "merchant"
) -> CartMandate:
    """Convert Fetch.ai RequestPayment to AP2 CartMandate."""
    pretty_print_model(
        request_payment,
        "(INPUT: Fetch.ai RequestPayment) Converting to AP2 CartMandate",
    )

    funds = request_payment.accepted_funds[0]  # Use first accepted funds

    # Build W3C PaymentRequest structure from Fetch.ai data
    # Use the RequestPayment reference as the cart ID if available
    cart_id = request_payment.reference

    pr: PaymentRequest = build_basic_payment_request(
        amount=float(funds.amount),
        currency=funds.currency,
        description=request_payment.description or "Payment request",
        supported_method=funds.payment_method,
        request_id=cart_id,
    )

    # Create CartMandate with expiry
    cart_expiry = (
        datetime.now(timezone.utc) + timedelta(seconds=request_payment.deadline_seconds)
    ).isoformat() + "Z"
    contents = CartContents(
        id=cart_id,  # Use the reference from RequestPayment as the cart ID
        payment_request=pr,
        user_cart_confirmation_required=True,
        cart_expiry=cart_expiry,
        merchant_name=merchant_name,
    )

    # Compute tamper-evident hash of cart contents
    cart_hash = compute_cart_hash(contents)
    cart_mandate = CartMandate(
        contents=contents,
        merchant_authorization="merchant_demo_auth",
        cart_hash=cart_hash,
    )

    pretty_print_model(cart_mandate, "(OUTPUT: AP2 CartMandate)")
    return cart_mandate


def commitpayment_to_paymentmandate(
    commit_payment: CommitPayment, agent_name: str
) -> PaymentMandate:
    """Convert Fetch.ai CommitPayment to AP2 PaymentMandate.

    This is the reverse conversion of paymentmandate_to_commitpayment.
    Note: This creates a synthetic PaymentMandate from CommitPayment data.
    """
    pretty_print_model(
        commit_payment,
        "(INPUT: Fetch.ai CommitPayment) Converting to AP2 PaymentMandate",
    )

    # Create payment details total from CommitPayment funds
    total_amount = PaymentCurrencyAmount(
        currency=commit_payment.funds.currency, value=float(commit_payment.funds.amount)
    )
    # Use CommitPayment description for the payment item label if available
    label = commit_payment.description or "Total"
    payment_details_total = PaymentItem(label=label, amount=total_amount)

    # Create payment response with the transaction token
    payment_response = PaymentResponse(
        request_id=commit_payment.transaction_id,
        method_name=commit_payment.funds.payment_method,
        details={"transaction_token": commit_payment.transaction_id},
    )

    # Build payment mandate contents
    payment_mandate_contents = PaymentMandateContents(
        payment_mandate_id=commit_payment.transaction_id,
        payment_details_id=commit_payment.reference or "",
        payment_details_total=payment_details_total,
        payment_response=payment_response,
        merchant_agent=agent_name,
    )

    # Compute hash for the payment mandate
    payment_mandate_hash = compute_payment_mandate_hash(payment_mandate_contents)

    payment_mandate = PaymentMandate(
        payment_mandate_contents=payment_mandate_contents,
        payment_mandate_hash=payment_mandate_hash,
        user_authorization="user_demo_auth",
    )

    pretty_print_model(payment_mandate, "(OUTPUT: AP2 PaymentMandate)")
    return payment_mandate


def rejectpayment_to_denycartmandate(reject_payment: RejectPayment) -> DenyCartMandate:
    """Convert Fetch.ai RejectPayment to AP2 DenyCartMandate."""
    pretty_print_model(
        reject_payment,
        "(INPUT: Fetch.ai RejectPayment) Converting to AP2 DenyCartMandate",
    )

    deny_cart_mandate = DenyCartMandate(reason=reject_payment.reason)

    pretty_print_model(deny_cart_mandate, "(OUTPUT: AP2 DenyCartMandate)")
    return deny_cart_mandate


def completepayment_to_paymentsuccess(
    complete_payment: CompletePayment,
) -> PaymentSuccess:
    """Convert Fetch.ai CompletePayment to AP2 PaymentSuccess."""
    pretty_print_model(
        complete_payment,
        "(INPUT: Fetch.ai CompletePayment) Converting to AP2 PaymentSuccess",
    )

    payment_success = PaymentSuccess(
        transaction_id=complete_payment.transaction_id or "unknown_transaction"
    )

    pretty_print_model(payment_success, "(OUTPUT: AP2 PaymentSuccess)")
    return payment_success


def cancelpayment_to_paymentfailure(cancel_payment: CancelPayment) -> PaymentFailure:
    """Convert Fetch.ai CancelPayment to AP2 PaymentFailure."""
    pretty_print_model(
        cancel_payment,
        "(INPUT: Fetch.ai CancelPayment) Converting to AP2 PaymentFailure",
    )

    payment_failure = PaymentFailure(
        transaction_id=cancel_payment.transaction_id or "unknown_transaction",
        reason=cancel_payment.reason,
    )

    pretty_print_model(payment_failure, "(OUTPUT: AP2 PaymentFailure)")
    return payment_failure


# ===================== A2A <-> FETCH.AI PIPELINE CONVERTERS =====================


def a2a_cartmandate_to_fetchai_requestpayment(
    a2a_msg: Message, recipient: str
) -> RequestPayment:
    """Convert A2A message with CartMandate to Fetch.ai RequestPayment.

    Args:
        a2a_msg: A2A Message containing CartMandate data
        recipient: Recipient address for Fetch.ai message

    Returns:
        Fetch.ai RequestPayment message
    """
    cart_mandate = extract_ap2_mandate_from_a2a(a2a_msg, CartMandate)
    return cartmandate_to_requestpayment(cart_mandate, recipient)  # type: ignore


def a2a_paymentmandate_to_fetchai_commitpayment(
    a2a_msg: Message, recipient: str
) -> CommitPayment:
    """Convert A2A message with PaymentMandate to Fetch.ai CommitPayment.

    Args:
        a2a_msg: A2A Message containing PaymentMandate data
        recipient: Recipient address for Fetch.ai message

    Returns:
        Fetch.ai CommitPayment message
    """
    payment_mandate = extract_ap2_mandate_from_a2a(a2a_msg, PaymentMandate)
    return paymentmandate_to_commitpayment(payment_mandate, recipient)  # type: ignore


def fetchai_requestpayment_to_a2a_cartmandate(
    request_payment: RequestPayment,
    context_id: str | None = None,
    task_id: str | None = None,
    merchant_name: str = "merchant",
) -> Message:
    """Convert Fetch.ai RequestPayment to A2A message with CartMandate.

    Args:
        request_payment: Fetch.ai RequestPayment message
        request_id: Request ID for AP2 message
        context_id: Optional A2A context ID
        task_id: Optional A2A task ID
        merchant_name: Merchant name for CartMandate

    Returns:
        A2A Message containing CartMandate data
    """
    cart_mandate = requestpayment_to_cartmandate(request_payment, merchant_name)
    return wrap_ap2_mandate_in_a2a(cart_mandate, context_id, task_id)


def fetchai_commitpayment_to_a2a_paymentmandate(
    commit_payment: CommitPayment,
    request_id: str,
    context_id: str | None = None,
    task_id: str | None = None,
    agent_name: str = "agent",
) -> Message:
    """Convert Fetch.ai CommitPayment to A2A message with PaymentMandate.

    Args:
        commit_payment: Fetch.ai CommitPayment message
        request_id: Request ID for AP2 message
        context_id: Optional A2A context ID
        task_id: Optional A2A task ID
        agent_name: Agent name for PaymentMandate

    Returns:
        A2A Message containing PaymentMandate data
    """
    payment_mandate = commitpayment_to_paymentmandate(commit_payment, agent_name)
    return wrap_ap2_mandate_in_a2a(payment_mandate, context_id, task_id)


__all__ = [
    # AP2 data keys
    "CART_MANDATE_KEY",
    "PAYMENT_MANDATE_KEY",
    # Generic A2A functions
    "extract_ap2_mandate_from_a2a",
    "wrap_ap2_mandate_in_a2a",
    # A2A <-> Fetch.ai pipeline converters
    "a2a_cartmandate_to_fetchai_requestpayment",
    "a2a_paymentmandate_to_fetchai_commitpayment",
    "fetchai_requestpayment_to_a2a_cartmandate",
    "fetchai_commitpayment_to_a2a_paymentmandate",
    # Utility functions
    "expiry_to_deadline_seconds",
    # AP2 -> Fetch.ai conversions
    "cartmandate_to_requestpayment",
    "paymentmandate_to_commitpayment",
    "denycartmandate_to_rejectpayment",
    "paymentsuccess_to_completepayment",
    "paymentfailure_to_cancelpayment",
    # Fetch.ai -> AP2 conversions
    "requestpayment_to_cartmandate",
    "commitpayment_to_paymentmandate",
    "rejectpayment_to_denycartmandate",
    "completepayment_to_paymentsuccess",
    "cancelpayment_to_paymentfailure",
]
