"""Dialogue protocol."""
from enum import Enum
from uuid import UUID

from pydantic import Field

from uagents import Model, Protocol, Context, Agent


NOTES = """
- A dialogue is a sequence of messages
- Each dialogue has a unique identifier
- A dialogue is identified by a DialogueLabel
- A dialogue will have a list of messages
- A dialogue will have a lifetime
- A dialogue will always have 1 "init" state in the beginning and a "finish"
  state in the end

Q: where to store the messages? Separate from ctx.storage?
Q: how to handle the lifetime of the dialogues? Block or time based?

OPL:
- Currently the layer of abstraction is not clear. A dialogue should either be
  use-case specific or protocol specific. Right now, it is a mix of both.
  -> Performatives should be configurable
"""


class Performative(str, Enum):
    INIT = "init"
    ACCEPT = "accept"
    DECLINE = "decline"
    MESSAGE = "message"
    FINISH = "finish"


class DialogueMessage(Model):
    performative: Performative = Field(
        description=("Description of what is being done (may be defined by a protocol)")
    )
    contents: dict = Field(
        description=(
            "Content of the message. " "This will vary based on the Performative."
        )
    )
    is_incoming: bool = Field(
        description=("True if the message is incoming, False if outgoing"),
        default=False,
    )
    target: str = Field(
        description=("Address of the agent that is the target of the message")
    )
    sender: str = Field(
        description=("Address of the agent that is the sender of the message")
    )


# To give the dialogue a context and to enable dialogue comparison
class DialogueLabel(Model):
    dialogue_reference: UUID = Field(description="Id of the dialogue")
    dialogue_starter: str = Field(
        description="Address of the agent that started the dialogue"
    )
    dialogue_receiver: str = Field(
        description="Address of the agent that is the receiver of the dialogue"
    )


# The actual message that will be sent to the other agent
# May need some more fields
class DialogueStarter(Model):
    pass


class DialogueWrapper(Model):
    dialogue_label: DialogueLabel
    dialogue_message: DialogueMessage


dialogue_protocol = Protocol(name="dialogue", version="0.1")


@dialogue_protocol.on_message(DialogueWrapper, DialogueWrapper)
async def handle_dialogue_message(
    ctx: Context, sender: str, msg: DialogueWrapper
) -> None:
    pass


class Dialogue:
    """
    - This should be the local representation of the dialogue.
    - Each participant will have its own instance of this class per dialogue.
    - A storage will contain all the dialogues that took place, which may be
      automatically deleted after a certain amount of time.
    - The dialogue will be identified by a DialogueLabel
    - is meant to simplify the handling of individual messages
    """

    def __init__(self, dialogue_id: UUID) -> None:
        self.id = dialogue_id  # session id of the dialogue
        # one dialogue id can have multiple session ids
        self.sessions = list[UUID]
        self.label = DialogueLabel(dialogue_reference=dialogue_id)
        self.rules = dict[Model, list[Model]]
        # which messages are allowed (handled model, list of replies)
        self.messages = list[(str, DialogueMessage)]  # message storage
        self.lifetime = 0

    def _create_msg_handler(self, msg: DialogueMessage) -> None:
        # check internal state
        pass

    def generate_digest(self) -> str:
        # generate a digest of the dialogue to be able to distinguish between
        # digest needs to include rules (models + interactions, ^= protocol)
        pass

    def setup(self):
        for r in self.rules:
            self._create_msg_handler(r)
        # add states
        # add message handlers
        pass


class PaymentDialogue(Dialogue):
    def __init__(self, dialogue_id: UUID) -> None:
        super().__init__(dialogue_id)
        self.rules = {
            DialogueStarter: [DialogueMessage],
            DialogueMessage: [DialogueMessage],
        }

    @classmethod
    def create(cls, dialogue_id: UUID) -> "PaymentDialogue":
        dialogue = cls(dialogue_id)
        dialogue.setup()
        return dialogue


payment = PaymentDialogue()


@payment.create(model=x, state=n, replies=y)
async def handle_payment(ctx: Context, sender: str, msg: DialogueMessage) -> None:
    pass


# ------
test_dialogue = Dialogue(UUID(1234))


# reuse decorators from Protocol?
@test_dialogue.on_state()
@test_dialogue.on_message(state=n, model=x, replies=y)


# attach functions to states separately?
async def function1():
    pass


test_dialogue.add_state("state1", function1, Model)

# attach dialogue to agent just like Protocol?
agent.include(test_dialogue)

NOTES2 = """
- msg has a session id
- we can use this session id to identify the dialogue
- one dialogue id can have multiple messages and ids

- less interest in generic solution
- we focus on set of structures -> to come up with client abstractions
- time log confirmation dialogue
- see dialogue as a blueprint for protocols

- dialogue stores only the rules
- you would still need to define the states and message handlers

- try to simplify the handling of individual messages
- single model for state (across whole flow or dialogue)
- dialogue would be a layer on top of  protocols and messages

- dialogue object has custom set of decorators (to build on the learnings)

start with:
- simple dialogue with simple rules
- query -> response -> accept/decline -> finish
- success, failure, timeout, retry
"""


# message needed to synchronize the dialogue partners
class DialogueStatus(Model):
    status: str


agent = Agent()
agent.on_message(DialogueStatus, DialogueStatus)


x = Protocol(name="dialogue", version="0.1")
x.on_message(DialogueStatus, DialogueStatus)


@dialogue_protocol.on_message(DialogueStatus, DialogueStatus, "INIT")
async def bla1(ctx: Context, sender: str, msg: DialogueStatus) -> None:
    pass


@dialogue_protocol.on_message(DialogueStatus, DialogueStatus, "MESSAGE")
async def bla2(ctx: Context, sender: str, msg: DialogueStatus) -> None:
    pass


@dialogue_protocol.on_message(DialogueStatus, DialogueStatus, "ACCEPT")
async def bla3(ctx: Context, sender: str, msg: DialogueStatus) -> None:
    pass


@dialogue_protocol.on_message(DialogueStatus, DialogueStatus, "FINISH")
async def bla4(ctx: Context, sender: str, msg: DialogueStatus) -> None:
    pass
