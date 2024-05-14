"""
Specific dialogue class the exchequer functionality.

The contents of this file are to be shared between the agents that want to
use this dialogue. This defines the structure of the specific dialogue and
the messages that are expected to be exchanged.
"""

from datetime import datetime
import json
from typing import Optional, Type
from warnings import warn

import requests
from uagents import Model
from uagents.context import Context
from uagents.experimental.dialogues import Dialogue, Edge, Node

from .clients import get_client  # pylint: disable=relative-beyond-top-level

EXCHEQUER_URL = "http://localhost:8000/v1/payments/"
# EXCHEQUER_URL = "https://staging.agentverse.ai/v1/payments/"
EXCHEQUER_ACCOUNTS = "accounts"
EXCHEQUER_EXCHANGE = "exchanges"

PAYER_TOKEN = get_client("client_2")["token"]
PAYEE_TOKEN = get_client("client_3")["token"]


# define dialogue messages; each transition needs a separate message
class PaymentRequest(Model):
    requester_id: str  # the id of the agent that requested the payment
    subject: str
    amount: int


class PaymentCommitment(Model):
    exchange_id: str


class PaymentComplete(Model):
    exchange_id: str


class PaymentSettled(Model):
    exchange_id: str


class PaymentRejected(Model):
    subject: str


# Node definition for the dialogue states
default_state = Node(
    name="Default State",
    description="",
    initial=True,
)
payment_requested = Node(
    name="Payment requested",
    description="",
)
payment_committed = Node(
    name="Payment committed",
    description="",
)
payment_completed = Node(
    name="Payment completed",
    description="",
)  # service provided here as well
exchequer_concluded = Node(
    name="Exchequer concluded",
    description="",
)

# Edge definition for the dialogue transitions
request_payment = Edge(
    name="Request Payment",
    description="",
    parent=default_state,
    child=payment_requested,
)
commit_payment = Edge(
    name="Commit Payment",
    description="",
    parent=payment_requested,
    child=payment_committed,
)
complete_payment = Edge(
    name="Complete Payment",
    description="",
    parent=payment_committed,
    child=payment_completed,
)
conclude_payment = Edge(
    name="Conclude Payment",
    description="",
    parent=payment_completed,
    child=exchequer_concluded,
)
reject_payment = Edge(
    name="Reject Payment",
    description="",
    parent=payment_requested,
    child=exchequer_concluded,
)
reject_payment = Edge(
    name="Reject Payment",
    description="",
    parent=payment_committed,
    child=exchequer_concluded,
)


async def get_balance(token: str):
    try:
        response = requests.get(
            url=EXCHEQUER_URL + EXCHEQUER_ACCOUNTS,
            headers={"Authorization": f"bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data["balances"][0]
    except requests.exceptions.RequestException as err:
        print("Error:", err)
    return None


async def lock_funds(token: str, requester_id: str, amount: int):
    try:
        response = requests.post(
            url=EXCHEQUER_URL + EXCHEQUER_EXCHANGE,
            json={
                "counterparty": requester_id,
                "amount": f"{amount}",
                "currency": "CRE",
                "confirmation_window": 10,
                "completion_window": 20,
                "conclusion_window": 30,
                "expected_completer": requester_id,
            },
            headers={"Authorization": f"bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data["exchange_id"]
    except requests.exceptions.RequestException as err:
        print("failed to create an exchange:", err)
    return None


async def get_exchange(exchange_id: str):
    try:
        response = requests.get(
            url=EXCHEQUER_URL + EXCHEQUER_EXCHANGE + f"/{exchange_id}",
            headers={"Authorization": f"bearer {PAYER_TOKEN}"},
            timeout=10,
        )
        # TODO import exchange object for typing?
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as err:
        print("failed to get exchange:", err)
    return None


async def confirm_exchange(exchange_id: str):
    try:
        requests.post(
            url=EXCHEQUER_URL + EXCHEQUER_EXCHANGE + f"/{exchange_id}/confirm",
            headers={"Authorization": f"bearer {PAYEE_TOKEN}"},
            timeout=10,
        )
    except requests.exceptions.RequestException as err:
        print("failed to confirm exchange:", err)


async def complete_exchange(exchange_id: str):
    try:
        requests.post(
            url=EXCHEQUER_URL + EXCHEQUER_EXCHANGE + f"/{exchange_id}/complete",
            json={"payment_amount": 40, "refund_amount": 10},
            headers={"Authorization": f"bearer {PAYEE_TOKEN}"},
            timeout=10,
        )
    except requests.exceptions.RequestException as err:
        print("failed to complete exchange:", err)


async def default(
    ctx: Context,
    _sender: str,
    _msg: Type[Model],
):
    ctx.logger.info("<<do your own stuff here>>")
    # ctx.logger.debug(msg)
    # warn(
    #     "There is no handler for this message, please add your own logic.",
    #     RuntimeWarning,
    #     stacklevel=2,
    # )


class Balance(Model):
    total: int = 0
    locked: int = 0
    available: int = 0
    currency: str = "CRE"
    updated_at: Optional[datetime] = None


class ExchequerError(Exception):
    """Exceptions when using Exchequer"""

    def __init__(self, message="Exchequer: Unexpected Error") -> None:
        self.message = message
        super().__init__(self.message)


# define default behaviour for individual dialogue edges
# TODO move this into the Dialogue class so it can be accessed. Maybe use decorators as well?


# TODO abstract or ommit?
class ExchequerDialogue(Dialogue):
    """
    The ExchequerDialogue class defines the structure of the dialogue necessary
    to facilitate the exchequer functionality.
    Most of the functionality will be handled by the dialogue class itself so
    only some specific handlers need to be implemented.
    """

    # TODO let edge functions only return but not yet send messages?
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
        super().__init__(
            name="ExchequerDialogue",
            version=version,
            agent_address=agent_address,
            nodes=[
                default_state,
                payment_requested,
                payment_committed,
                payment_completed,
                exchequer_concluded,
            ],
            edges=[
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

    #
    # Individual Exchequer Dialogue Decorators
    #

    def on_request(self, msg: type[Model]):
        """
        This message handler is triggered when a PaymentRequest message is received.
        Any logic to decide whether the request should be accepted is to be implemented here.
        """
        return super()._on_state_transition(request_payment.name, msg)

    def on_commit(self, msg: type[Model]):
        """
        This message handler is triggered whe a PaymentCommitment message is received.
        Use this this to initiate your completion process (e.g., service provisioning),
        or to mark this transaction as 'ready for completion'.
        Note that you need to explicitly send the PaymentComplete message here if you
        immediately provide the service, or to trigger its sending whenever you actually
        provided your service.
        """
        return super()._on_state_transition(commit_payment.name, msg)

    def on_complete(self, msg: type[Model]):
        """
        This message handler is triggered when a PaymentComplete message is received.
        Use this if you need dedicated reactions such as notifications.
        """
        return super()._on_state_transition(complete_payment.name, msg)

    def on_conclude(self, msg: type[Model]):
        """
        This message handler is triggered when a PaymentSettled message is received,
        which probably makes no sense
        """
        return super()._on_state_transition(conclude_payment.name, msg)
