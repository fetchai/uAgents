"""Specific dialogue class for the chit-chat dialogue."""
from uagents.experimental.dialogues import Dialogue, Node, Edge

# Node definition for the dialogue states
chatting_state = Node(
    name="Chit Chatting",
    description="While in this state, more messages can be exchanged.",
)
end_state = Node(
    name="Concluded",
    description="This is the state after the dialogue has been concluded and "
    "no more messages will be accepted.",
)

# Edge definition for the dialogue transitions
start_dialogue = Edge(
    name="Start Dialogue",
    description=(
        "A message that initiates a ChitChat conversation and provides "
        "any information needed to set the context and let the receiver "
        "decide whether to accept or directly end this conversation."
    ),
    parent=None,
    child=chatting_state,
)
cont_dialogue = Edge(
    name="Continue Dialogue",
    description=(
        "A general message structure to exchange information without "
        "annotating further states or limiting the message flow in any way."
    ),
    parent=chatting_state,
    child=chatting_state,
)
end_dialogue = Edge(
    name="End Dialogue",
    description=(
        "A final message that can be sent at any time by either party "
        "to finish this dialogue."
    ),
    parent=chatting_state,
    child=end_state,
)


class SimpleChitChatDialogue(Dialogue):
    """
    The SimpleChitChatDialogue provides a simple pattern that allows 2 parties
    to exchange an arbitrary number of "ChitChat" messages
    """

    def __init__(
        self,
        version: str | None = None,
        agent_address: str | None = None,
    ) -> None:
        super().__init__(
            name="ChitChatDialogue_simple",
            version=version,
            agent_address=agent_address,
            nodes=[
                chatting_state,
                end_state,
            ],
            edges=[
                start_dialogue,
                cont_dialogue,
                end_dialogue,
            ],
        )
