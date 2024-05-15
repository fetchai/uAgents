"""
This integration provides all necessary definitions to build use cases around negotiating, reserving
and paying any kind of resources between a provider and a consumer.

This entails the following:
- resource:
- service provider:
- consumer

prerequisits:
- credits / exchequer

How To
- provider needs to implement the following handlers:
  -
- consumer needs to implement the following handlers:
  -

The contents of this file are to be shared between the agents that want to
use this dialogue. This defines the structure of the specific dialogue and
the messages that are expected to be exchanged.
"""

import json
from typing import Any, Dict
from warnings import warn

from uagents import Model
from uagents.context import Context
from uagents.experimental.dialogues import Dialogue, Edge, Node

from .clients import get_client  # pylint: disable=relative-beyond-top-level
from .exchequer import (
    Balance,
    ExchequerError,
    PaymentCommitment,
    PaymentComplete,
    PaymentRejected,
    PaymentRequest,
    PaymentSettled,
    complete_exchange,
    confirm_exchange,
    default,
    get_balance,
    get_exchange,
    lock_funds,
    payment_requested,
    payment_committed,
    payment_completed,
    exchequer_concluded,
    commit_payment,
    complete_payment,
    conclude_payment,
    reject_payment,
)

EXCHEQUER_URL = "http://localhost:8000/v1/payments/"
# EXCHEQUER_URL = "https://staging.agentverse.ai/v1/payments/"
EXCHEQUER_ACCOUNTS = "accounts"
EXCHEQUER_EXCHANGE = "exchanges"

PAYER_TOKEN = get_client("client_2")["token"]
PAYEE_TOKEN = get_client("client_3")["token"]


# Base dialogue messages. Check <TODO> to understand which messages to extend for customization


class ResourceRequest(Model):
    quantity: int
    type: str


class ResourceAvailability(Model):
    available: int
    type: str
    price: int  # price for a single resource
    options: Dict[
        str, Any
    ]  # describes any options to chose from for the given type of resource


class ResourceRerservation(Model):
    type: str
    quantity: int
    options: Dict[str, Any]


class ReservationReject(Model):
    reason: str


# Node definition for the dialogue states
default_state = Node(
    name="Default State",
    description="",
    initial=True,
)
resource_requested = Node(
    name="Resource requested",
    description="",
)
resource_availability_given = Node(
    name="Resource availability returned",
    description="",
)
resource_reserved = Node(
    name="Resource reserved",
    description="",
)
resource_rejected = Node(
    name="Resource rejected",
    description="",
)

# Edge definition for the dialogue transitions
request_resource_availability = Edge(
    name="Request Resource",
    description="",
    parent=default_state,
    child=resource_requested,
)
return_availability = Edge(
    name="Return Availability",
    description="",
    parent=resource_requested,
    child=resource_availability_given,
)
no_availability = Edge(
    name="No availability",
    description="",
    parent=resource_requested,
    child=resource_rejected,
)
reserve_resource = Edge(
    name="Reserve Resource",
    description="",
    parent=resource_availability_given,
    child=resource_reserved,
)
reject_reservation = Edge(
    name="Reject reservation",
    description="",
    parent=resource_reserved,
    child=resource_rejected,
)
request_payment = Edge(
    name="Request Payment",
    description="",
    parent=resource_reserved,
    child=payment_requested,
)  # TODO is this edge overwrite working?


class ResourcePaymentDialogue(Dialogue):
    """
    Generic resource discovery and payment dialogue.
    Description tbd
    """

    #
    # Resource dialogue specific handlers
    #

    async def handle_resource_request(
        self, ctx: Context, sender: str, msg: ResourceRequest
    ):
        resource = ctx.storage.get("resources")[msg.type]
        available = resource["available"] or 0
        price = resource["price"] or 0

        if available == 0 or available < msg.quantity:
            await ctx.send(sender, ReservationReject(reason="Resource not available"))
        else:
            # in the case of service chaining, start a new dialogue with target services/resources here and set a timeout.
            # Basic requirements/considerations apply as for broadcast stateful logic (timeouts and possible states need to be tied to sessions)
            await ctx.send(
                sender,
                ResourceAvailability(
                    available=available, type=msg.type, price=price, options={}
                ),
            )

    async def handle_availability(
        self, ctx: Context, sender: str, msg: ResourceAvailability
    ):
        # wait for offers to be received and chose best

        bal = await get_balance(PAYER_TOKEN)
        if not bal:
            ctx.logger.debug("Exchequer: Failed to get account balance")
            return
        balance = Balance(**bal)
        ctx.logger.debug(f"Exchequer: Account balance: {balance}")
        # TODO refer to initially requested quantity
        qnty = 1
        if balance.available > msg.price * qnty:
            await ctx.send(
                sender, ResourceRerservation(type=msg.type, quantity=qnty, options={})
            )
        else:
            ctx.logger.debug(f"Exchequer: Not enough funds for offer from {sender}")

    async def handle_reservation(
        self, ctx: Context, sender: str, msg: ResourceRerservation
    ):
        resources = ctx.storage.get("resources")
        available = resources[msg.type]["available"]
        if available > 0:
            resources[msg.type]["available"] = available - 1
            ctx.storage.set("resources", resources)
            await ctx.send(
                sender,
                PaymentRequest(
                    requester_id=get_client("client_3")["id"],
                    amount=resources[msg.type]["amount"],
                    subject="Invoice #111 for resource",
                ),
            )
        else:
            ctx.logger.debug(f"Exchequer: Not resources available of type {msg.type}")

    #
    # Exchequer specific handlers (copied from exchequer.py as long as we don't have composability)
    #

    async def handle_payment_request(
        self, ctx: Context, sender: str, msg: PaymentRequest
    ):
        ctx.logger.debug("Exchequer: Received payment request")
        bal = await get_balance(PAYER_TOKEN)
        if not bal:
            ctx.logger.debug("Exchequer: Failed to get account balance")
            await ctx.send(
                sender, PaymentRejected(subject="Failed to get account balance")
            )
            return
        balance = Balance(**bal)
        ctx.logger.debug(f"Exchequer: Account balance: {balance}")
        if not balance or balance.available < msg.amount:
            ctx.logger.debug("Exchequer: Insufficient funds")
            await ctx.send(sender, PaymentRejected(subject=msg.subject))
            return

        exchange_id = await lock_funds(PAYER_TOKEN, msg.requester_id, msg.amount)
        ctx.logger.debug(f"Exchequer: Created exchange with id: {exchange_id}")
        if not exchange_id:
            ctx.logger.error("failed to create exchange")
            raise ExchequerError("Exchequer: Failed to create exchange")

        await ctx.send(sender, PaymentCommitment(exchange_id=exchange_id))

    async def handle_payment_commitment(
        self, ctx: Context, sender: str, msg: PaymentCommitment
    ):
        ctx.logger.debug(
            f"Exchequer: Received payment commitment for exchange_id: {msg.exchange_id}"
        )

        # check lock, verify IDs and amounts
        exchange = await get_exchange(msg.exchange_id)
        ctx.logger.debug(f"Exchequer: Exchange state: {exchange['state']}")

        if not exchange:
            ctx.logger.debug("Exchequer: Failed to get exchange")
            await ctx.send(sender, PaymentRejected(subject="Failed to get exchange"))
            return

        if exchange["state"] != "locked":
            ctx.logger.debug("Exchequer: Exchange is not locked")
            await ctx.send(sender, PaymentRejected(subject="Exchange is not locked"))
            return

        # TODO how to access dialogue instance here to use get_conversation instead?
        request_msg = self.get_conversation(ctx.session)[0]
        request_content = json.loads(request_msg["message_content"])
        amount_expected = request_content["amount"]
        amount_actual = exchange["total_amount"]
        if amount_actual != amount_expected:
            ctx.logger.debug(
                f"Exchequer: Unexpected amount in exchange: {amount_actual} (expected: {amount_expected}) "
            )
            await ctx.send(
                sender,
                PaymentRejected(
                    subject="Exchange amount not equaling requested amount"
                ),
            )
            return

        # TODO check exchange.counterparty == requester id
        # TODO check exchange.subject == requested subject

        # confirm & trust that Exchequer will work as intended
        ctx.logger.debug("Exchequer: Executing confirm")
        await confirm_exchange(msg.exchange_id)

        # complete
        ctx.logger.debug("Exchequer: <<< providing service >>>")
        warn("Service provided here as well", RuntimeWarning, stacklevel=2)

        ctx.logger.debug("Exchequer: Executing complete: taking 40, refunding 10")
        await complete_exchange(msg.exchange_id)  # payment done at this point

        # notify about complete
        await ctx.send(sender, PaymentComplete(exchange_id=msg.exchange_id))

    async def handle_payment_complete(
        self, ctx: Context, sender: str, msg: PaymentComplete
    ):
        ctx.logger.debug(
            f"Exchequer: Payment completed for exchange_id: {msg.exchange_id}"
        )

        # check complete and do some cleanup here on payer side
        exchange = await get_exchange(msg.exchange_id)
        ctx.logger.debug(f"Exchequer: Exchange state: {exchange['state']}")

        balance = await get_balance(PAYER_TOKEN)
        ctx.logger.debug(f"Exchequer: Account balance: {balance}")

        # wait till exchange is settled and funds are released
        await ctx.send(sender, PaymentSettled(exchange_id=msg.exchange_id))

    async def handle_payment_settled(
        self, ctx: Context, _sender: str, msg: PaymentSettled
    ):
        ctx.logger.debug(
            f"Exchequer: Payment should be settled now for exchange_id: {msg.exchange_id}"
        )
        # do some cleanup on payee side

    def __init__(
        self,
        version: str | None = None,
        agent_address: str | None = None,
    ) -> None:
        request_resource_availability.set_edge_handler(
            ResourceRequest, self.handle_resource_request
        )

        return_availability.set_edge_handler(
            ResourceAvailability, self.handle_availability
        )

        reserve_resource.set_edge_handler(ResourceRerservation, self.handle_reservation)

        request_payment.set_edge_handler(PaymentRequest, self.handle_payment_request)
        request_payment.set_message_handler(PaymentRequest, default)

        commit_payment.set_edge_handler(
            PaymentCommitment, self.handle_payment_commitment
        )
        commit_payment.set_message_handler(PaymentCommitment, default)

        complete_payment.set_edge_handler(PaymentComplete, self.handle_payment_complete)
        complete_payment.set_message_handler(PaymentComplete, default)

        conclude_payment.set_edge_handler(PaymentSettled, self.handle_payment_settled)
        conclude_payment.set_message_handler(PaymentSettled, default)

        reject_payment.set_message_handler(PaymentSettled, default)
        super().__init__(
            name="ExchequerDialogue",
            version=version,
            agent_address=agent_address,
            nodes=[
                default_state,
                resource_requested,
                resource_availability_given,
                resource_rejected,
                resource_reserved,
                payment_requested,
                payment_committed,
                payment_completed,
                exchequer_concluded,
            ],
            edges=[
                request_resource_availability,
                return_availability,
                no_availability,
                reserve_resource,
                reject_reservation,
                request_payment,
                commit_payment,
                complete_payment,
                conclude_payment,
            ],
        )
        # instantiation of the exchequer dialogue class should include authentication
        # based on the agent address or another method of authentication
        self.user_id = None
        self.user_token = None

    #
    # Individual Resource Dialogue Decorators
    #

    def on_resource_request(self, msg: type[Model]):
        return super()._on_state_transition(request_resource_availability.name, msg)
