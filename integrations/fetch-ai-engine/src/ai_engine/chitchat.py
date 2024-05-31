"""Specific dialogue class for the AI enabled chit-chat dialogue."""

from typing import Type, Optional

from uagents import Model
from uagents.experimental.dialogues import Dialogue, Node, Edge
from uagents.storage import StorageAPI


# Node definition for the dialogue states
init_state = Node(
    name="Initiated",
    description=(
        "This is the initial state of the dialogue that is only available at "
        "the receiving agent."
    ),
    initial=True,
)

chatting_state = Node(
    name="Chit Chatting",
    description="This is the state in which messages are exchanged.",
)
end_state = Node(
    name="Concluded",
    description="This is the state after the dialogue has been concluded.",
)


start_dialogue = Edge(
    name="Start dialogue",
    description=(
        "A message that initiates a ChitChat conversation and provides "
        "any information needed to set the context and let the receiver "
        "decide whether to accept or directly end this conversation."
    ),
    parent=init_state,
    child=chatting_state,
    metadata={
        "target": "user",
        "observable": True,
    },
)
cont_dialogue = Edge(
    name="Continue dialogue",
    description=(
        "This is the transition from one dialogue message to the next, "
        "i.e. for when the dialogue continues."
    ),
    parent=chatting_state,
    child=chatting_state,
    metadata={
        "target": "user",
        "observable": True,
    },
)
end_session = Edge(
    name="End dialogue",
    description=(
        "A final message that can be sent at any time by either party "
        "to finish this dialogue."
    ),
    parent=chatting_state,
    child=end_state,
    metadata={
        "target": "user",
        "observable": True,
    },
)


class ChitChatDialogue(Dialogue):
    """
    This is the specific definition of the rules for the chit-chat dialogue
    The rules will be predefined and the actual messages will be passed into it
    """

    def __init__(
        self,
        version: Optional[str] = None,
        storage: Optional[StorageAPI] = None,
    ) -> None:
        super().__init__(
            name="ChitChatDialogue",
            version=version,
            storage=storage,
            nodes=[
                init_state,
                chatting_state,
                end_state,
            ],
            edges=[
                start_dialogue,
                cont_dialogue,
                end_session,
            ],
        )

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
