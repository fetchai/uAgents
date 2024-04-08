"""Specific dialogue class for the chit-chat dialogue."""

from typing import Type

from uagents import Model
from uagents.experimental.dialogues import Dialogue, Edge, Node

# Node definition for the dialogue states
default_state = Node(
    name="Default State",
    description=(
        "This is the default state of the dialogue. Every session starts in "
        "this state and is automatically updated once the dialogue starts."
    ),
    initial=True,
)
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
    name="Initiate session",
    description="Every dialogue starts with this transition.",
    parent=default_state,
    child=init_state,
)
reject_session = Edge(
    name="Reject session",
    description=("This is the transition for when the dialogue is rejected"),
    parent=init_state,
    child=end_state,
)
start_dialogue = Edge(
    name="Start dialogue",
    description="This is the transition from initiated to chit chatting.",
    parent=init_state,
    child=chatting_state,
)
cont_dialogue = Edge(
    name="Continue dialogue",
    description=(
        "This is the transition from one dialogue message to the next, "
        "i.e. for when the dialogue continues."
    ),
    parent=chatting_state,
    child=chatting_state,
)
end_session = Edge(
    name="End session",
    description="This is the transition for when the session is ended.",
    parent=chatting_state,
    child=end_state,
)


class ChitChatDialogue(Dialogue):
    """
    This is the specific definition of the rules for the chit-chat dialogue
    The rules will be predefined and the actual messages will be passed into it
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
                default_state,
                init_state,
                chatting_state,
                end_state,
            ],
            edges=[
                init_session,
                reject_session,
                start_dialogue,
                cont_dialogue,
                end_session,
            ],
        )

    def on_initiate_session(self, model: Type[Model]):
        """
        This handler is triggered when the initial message of the
        dialogue is received. From here you can either accept or reject.
        Logic that is needed to complete any kind of handshake or considers
        global agent state should go here.
        """
        return super()._on_state_transition(init_session.name, model)

    def on_reject_session(self, model: Type[Model]):
        """
        This handler is triggered when a reject message is returned on
        the initial message.
        Implement this if you need to clean up session data.
        """
        return super()._on_state_transition(reject_session.name, model)

    def on_start_dialogue(self, model: Type[Model]):
        """
        This handler is triggered when an accept message is returned on
        the initial message.
        Include logic to complete any handshake on the sender side and
        prepare the actual message exchange.
        """
        return super()._on_state_transition(start_dialogue.name, model)

    def on_continue_dialogue(self, model: Type[Model]):
        """
        This handler is triggered for every incoming "chitchat" message
        once the session has been accepted.
        Any additional stateful information within a dialogue needs to be
        persisted explicitly to access it at a later point in the dialogue.
        """
        return super()._on_state_transition(cont_dialogue.name, model)

    def on_end_session(self, model: Type[Model]):
        """
        This handler is triggered once the other party has ended the dialogue.
        Any final conclusion or cleanup goes here.
        """
        return super()._on_state_transition(end_session.name, model)