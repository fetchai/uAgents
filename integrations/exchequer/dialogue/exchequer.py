"""
Specific dialogue class the exchequer functionality.

The contents of this file are to be shared between the agents that want to
use this dialogue. This defines the structure of the specific dialogue and
the messages that are expected to be exchanged.
"""

from typing import Type
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

PAYER_TOKEN = get_client("client_1")["token"]
PAYEE_TOKEN = get_client("client_2")["token"]


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
    msg: Type[Model],
):
    ctx.logger.debug(msg)
    # warn(
    #     "There is no handler for this message, please add your own logic.",
    #     RuntimeWarning,
    #     stacklevel=2,
    # )


async def handle_payment_request(ctx: Context, sender: str, msg: PaymentRequest):
    ctx.logger.debug("received payment request")
    balance = await get_balance(PAYER_TOKEN)
    ctx.logger.debug(f"account balance: {balance}")
    if not balance or balance < msg.amount:
        ctx.logger.debug("Insufficient funds")
        await ctx.send(sender, PaymentRejected(subject=msg.subject))
        return

    exchange_id = await lock_funds(PAYER_TOKEN, msg.requester_id, msg.amount)
    ctx.logger.debug(f"Created exchange with id: {exchange_id}")

    await ctx.send(sender, PaymentCommitment(exchange_id=exchange_id))


async def handle_payment_commitment(ctx: Context, sender: str, msg: PaymentCommitment):
    ctx.logger.debug(f"received payment commitment for exchange_id: {msg.exchange_id}")

    # check lock, verify IDs and amounts
    exchange = await get_exchange(msg.exchange_id)
    ctx.logger.debug(f"exchange state: {exchange['state']}")

    if exchange["state"] != "locked":
        ctx.logger.debug("Exchange is not locked")
        await ctx.send(sender, PaymentRejected(subject="Exchange is not locked"))
        return

    # confirm & trust that Exchequer will work as intended
    ctx.logger.debug("executing confirm")
    await confirm_exchange(msg.exchange_id)

    # complete
    ctx.logger.debug("<<< providing service >>>")
    warn("Service provided here as well", RuntimeWarning, stacklevel=2)

    ctx.logger.debug("executing complete: taking 40, refunding 10")
    await complete_exchange(msg.exchange_id)  # payment done at this point

    # notify about complete
    await ctx.send(sender, PaymentComplete(exchange_id=msg.exchange_id))


async def handle_payment_complete(ctx: Context, sender: str, msg: PaymentComplete):
    ctx.logger.debug(f"payment completed for exchange_id: {msg.exchange_id}")

    # check complete and do some cleanup here on payer side
    exchange = await get_exchange(msg.exchange_id)
    ctx.logger.debug(f"exchange state: {exchange['state']}")

    balance = await get_balance(PAYER_TOKEN)
    ctx.logger.debug(f"account balance: {balance}")

    # wait till exchange is settled and funds are released
    await ctx.send(sender, PaymentSettled(exchange_id=msg.exchange_id))


async def handle_payment_settled(ctx: Context, _sender: str, msg: PaymentSettled):
    ctx.logger.debug(
        f"payment should be settled now for exchange_id: {msg.exchange_id}"
    )
    # do some cleanup on payee side


# define default behaviour for individual dialogue edges
request_payment.set_edge_handler(PaymentRequest, handle_payment_request)
request_payment.set_message_handler(PaymentRequest, default)

commit_payment.set_edge_handler(PaymentCommitment, handle_payment_commitment)
commit_payment.set_message_handler(PaymentCommitment, default)

complete_payment.set_edge_handler(PaymentComplete, handle_payment_complete)
complete_payment.set_message_handler(PaymentComplete, default)

conclude_payment.set_edge_handler(PaymentSettled, handle_payment_settled)
conclude_payment.set_message_handler(PaymentSettled, default)

reject_payment.set_message_handler(PaymentSettled, default)


class ExchequerDialogue(Dialogue):
    """
    The ExchequerDialogue class defines the structure of the dialogue necessary
    to facilitate the exchequer functionality.
    Most of the functionality will be handled by the dialogue class itself so
    only some specific handlers need to be implemented.
    """

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

    # def on_continue_dialogue(self):
    #     """
    #     This handler is triggered for every incoming "chitchat" message
    #     once the session has been accepted.
    #     Any additional stateful information within a dialogue needs to be
    #     persisted explicitly to access it at a later point in the dialogue.
    #     """
    #     return super()._on_state_transition(
    #         cont_dialogue.name,
    #         ChitChatDialogueMessage,
    #     )
