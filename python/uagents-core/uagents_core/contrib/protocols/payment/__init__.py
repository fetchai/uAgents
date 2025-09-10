from uagents_core.models import Model
from uagents_core.protocol import ProtocolSpecification


class Funds(Model):
    # amount of funds
    amount: str

    # currency of the funds (USDC, FET, etc.)
    currency: str

    # payment method (skyfire, fet_direct)
    payment_method: str = "fet_direct"


class RequestPayment(Model):
    # funds accepted for the requested payment
    accepted_funds: list[Funds]

    # recipient address or identifier
    recipient: str

    # deadline for the payment request in seconds
    deadline_seconds: int

    # optional reference for the payment
    reference: str | None = None

    # optional description of the payment
    description: str | None = None

    # optional metadata for the payment
    metadata: dict[str, str | dict[str, str]] | None = None


class RejectPayment(Model):
    # optional reason for rejecting the payment
    reason: str | None = None


class CommitPayment(Model):
    # funds to be paid
    funds: Funds

    # recipient address or identifier
    recipient: str

    # unique transaction token or hash
    transaction_id: str

    # optional reference for the payment
    reference: str | None = None

    # optional description of the payment
    description: str | None = None

    # optional metadata for the payment
    metadata: dict[str, str | dict[str, str]] | None = None


class CancelPayment(Model):
    # unique transaction token or hash
    transaction_id: str | None = None

    # optional reason for canceling the payment
    reason: str | None = None


class CompletePayment(Model):
    # unique transaction token or hash
    transaction_id: str | None = None


payment_protocol_spec = ProtocolSpecification(
    name="AgentPaymentProtocol",
    version="0.1.0",
    interactions={
        RequestPayment: {CommitPayment, RejectPayment},
        CommitPayment: {CompletePayment, CancelPayment},
        CompletePayment: set(),
        CancelPayment: set(),
        RejectPayment: set(),
    },
    roles={
        "seller": {CommitPayment, RejectPayment},
        "buyer": {RequestPayment, CancelPayment, CompletePayment},
    },
)
