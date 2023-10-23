"""Specific dialogue class for the chit-chat dialogue."""
from typing import Type

from uagents import Model
from uagents.experimental.dialogues import Dialogue, Edge, Node

# Node definition for the dialogue states
default_state = Node(
    name="Default State",
    description=(
        "This is the default state of the dialogue. Every session starts in "
        "this state and is automatically updated once ."
    ),
    starter=True,
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
    description="This is the transition to start the dialogue",
    parent=None,
    child=init_state,
)
reject_session = Edge(
    name="reject_session",
    description=(
        "This is the transition for when the session is rejected or not needed."
    ),
    parent=init_state,
    child=end_state,
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
        """Explicit state transition for the initiate_session event."""
        return super()._on_state_transition(init_session.name, model)

    def on_reject_session(self, model: Type[Model]):
        """Explicit state transition for the reject_session event."""
        return super()._on_state_transition(reject_session.name, model)

    def on_start_dialogue(self, model: Type[Model]):
        """Explicit state transition for the start_dialogue event."""
        return super()._on_state_transition(start_dialogue.name, model)

    def on_continue_dialogue(self, model: Type[Model]):
        """Explicit state transition for the continue_dialogue event."""
        return super()._on_state_transition(cont_dialogue.name, model)

    def on_end_session(self, model: Type[Model]):
        """Explicit state transition for the end_session event."""
        return super()._on_state_transition(end_session.name, model)
