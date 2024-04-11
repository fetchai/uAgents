"""
Specific dialogue class for the chit-chat dialogue.

The contents of this file are to be shared between the agents that want to
use this dialogue. This defines the structure of the specific dialogue and
the messages that are expected to be exchanged.
"""

from warnings import warn

from uagents import Model
from uagents.context import Context
from uagents.experimental.dialogues import Dialogue, Edge, Node


# define dialogue messages; each transition needs a separate message
class InitiateChitChatDialogue(Model):
    pass


class AcceptChitChatDialogue(Model):
    pass


class ChitChatDialogueMessage(Model):
    text: str


class ConcludeChitChatDialogue(Model):
    pass


class RejectChitChatDialogue(Model):
    pass


# Node definition for the dialogue states
default_state = Node(
    name="Default State",
    description=(
        "This is the default state of the dialogue. Every session starts in "
        "this state and is automatically updated once ."
    ),
    initial=True,
)  # currently not used as states are measured by the edges
init_state = Node(
    name="Initiated",
    description=(
        "This is the initial state of the dialogue that is only available at "
        "the receiving agent."
    ),
)
chatting_state = Node(
    name="Chit Chatting",
    description="This is the state in which messages are exchanged.",
)
end_state = Node(
    name="Concluded",
    description="This is the state after the dialogue has been concluded.",
)

# Edge definition for the dialogue transitions
init_session = Edge(
    name="initiate_session",
    description="Every dialogue starts with this transition.",
    parent=None,
    child=init_state,
)
start_dialogue = Edge(
    name="start_dialogue",
    description="This is the transition from initiated to chit chatting.",
    parent=init_state,
    child=chatting_state,
)
cont_dialogue = Edge(
    name="continue_dialogue",
    description=(
        "This is the transition from one dialogue message to the next, "
        "i.e. for when the dialogue continues."
    ),
    parent=chatting_state,
    child=chatting_state,
)
end_session = Edge(
    name="end_session",
    description="This is the transition for when the session is ended.",
    parent=chatting_state,
    child=end_state,
)


# define default behaviour for individual dialogue edges
# only the interaction that requires input from the user is exposed, making the
# other parts of the dialogue more robust and easier to maintain
async def start_chitchat(
    ctx: Context,
    sender: str,
    _msg: type[Model],
):
    ctx.logger.info(f"Received init message from {sender}. Accepting Dialogue.")
    await ctx.send(sender, AcceptChitChatDialogue())


async def accept_chitchat(
    ctx: Context,
    sender: str,
    _msg: type[Model],
):
    ctx.logger.info(
        f"Dialogue session with {sender} was accepted. "
        "I'll say 'Hello!' to start the ChitChat"
    )
    await ctx.send(sender, ChitChatDialogueMessage(text="Hello!"))


async def conclude_chitchat(
    ctx: Context,
    sender: str,
    _msg: type[Model],
):
    ctx.logger.info(f"Received conclude message from: {sender}; accessing history:")
    ctx.logger.info(ctx.dialogue)


async def default(
    _ctx: Context,
    _sender: str,
    _msg: type[Model],
):
    warn(
        "There is no handler for this message, please add your own logic by "
        "using the `on_continue_dialogue` decorator.",
        RuntimeWarning,
        stacklevel=2,
    )


init_session.set_default_behaviour(InitiateChitChatDialogue, start_chitchat)
start_dialogue.set_default_behaviour(AcceptChitChatDialogue, accept_chitchat)
cont_dialogue.set_default_behaviour(ChitChatDialogueMessage, default)
end_session.set_default_behaviour(ConcludeChitChatDialogue, conclude_chitchat)


class ChitChatDialogue(Dialogue):
    """
    This is the specific definition of the rules for the chit-chat dialogue
    The rules will be predefined and the actual messages will be passed into it.

    In this specific instance of the ChitChatDialogue, some parts of the dialogue
    are hardcoded, such as the initial message and the response to it.
    This is done to demonstrate that the dialogue can be defined in a way for
    developers to only focus on the parts that are relevant to them.
    """

    def __init__(
        self,
        version: str | None = None,
        agent_address: str | None = None,
    ) -> None:
        super().__init__(
            name="ChitChatDialogue",
            version=version,
            agent_address=agent_address,
            nodes=[
                init_state,
                chatting_state,
                end_state,
            ],
            edges=[
                init_session,
                start_dialogue,
                cont_dialogue,
                end_session,
            ],
        )

    def on_continue_dialogue(self):
        """
        This handler is triggered for every incoming "chitchat" message
        once the session has been accepted.
        Any additional stateful information within a dialogue needs to be
        persisted explicitly to access it at a later point in the dialogue.
        """
        return super()._on_state_transition(
            cont_dialogue.name,
            ChitChatDialogueMessage,
        )
