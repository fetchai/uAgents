"""Specific dialogue class for the chit-chat dialogue."""
from uagents.experimental.dialogues import Dialogue, Node, Edge

state0 = Node(
    name="Default State",
    description="This is the default state of the dialogue.",
    starter=True,
)

# Node definition for the dialogue states
state1 = Node(
    name="Initiated",
    description="This is the initial state of the dialogue.",
)
state2 = Node(
    name="Chit Chatting",
    description="This is the state in which messages are exchanged.",
)
state3 = Node(
    name="Concluded",
    description="This is the state after the dialogue has been concluded.",
)

# Edge definition for the dialogue transitions
transition1 = Edge(
    name="Initiate Session",
    description="This is the transition to start the dialogue",
    parent=None,
    child=state1,
)
transition2 = Edge(
    name="Session Rejected / Not Needed",
    description=(
        "This is the transition for when the session is rejected or not needed."
    ),
    parent=state1,
    child=state3,
)
transition3 = Edge(
    name="Dialogue Started",
    description="This is the transition from initiated to chit chatting.",
    parent=state1,
    child=state2,
)
transition4 = Edge(
    name="Dialogue Continues",
    description=(
        "This is the transition from one dialogue message to the next, "
        "i.e. for when the dialogue continues."
    ),
    parent=state2,
    child=state2,
)
transition5 = Edge(
    name="Hang Up / End Session",
    description="This is the transition for when the session is ended.",
    parent=state2,
    child=state3,
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
                state1,
                state2,
                state3,
            ],
            edges=[
                transition1,
                transition2,
                transition3,
                transition4,
                transition5,
            ],
        )
