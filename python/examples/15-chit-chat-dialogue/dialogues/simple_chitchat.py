"""Specific dialogue class for the chit-chat dialogue."""
from uagents.experimental.dialogues import Dialogue, Node, Edge

# Node definition for the dialogue states
waiting_state = Node(
    name="Waiting",
    description=(
        "This is the default state of the dialogue. Every session starts in "
        "this state and is automatically updated once a transition to start or "
        "continue a dialogue is triggered."
    ),
    starter=True,
)  # currently not used as states are measured by the edges
# init_state = Node(
#     name="Initiated",
#     description=(
#         "This is the initial state of the dialogue that is only available at "
#         "the receiving agent."
#     ),
# )
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
# init_session = Edge(
#     name="Initiate Session",
#     description="This is the transition to start the dialogue",
#     parent=None,
#     child=init_state,
# )
# reject_session = Edge(
#     name="Session Rejected / Not Needed",
#     description=(
#         "This is the transition for when the session is rejected or not needed."
#     ),
#     parent=init_state,
#     child=end_state,
# )
start_dialogue = Edge(
    name="Start Dialogue",
    description=(
        "A message that initiates a ChitChat conversation and provides "
        "any information needed to set the context and let the receiver "
        "decide whether to accept or directly end this conversation."
    ),
    parent=waiting_state,
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
        "A final message that can be sent at any time by either party at any"
        "time to finish this dialogue."
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
            name="ChitChatDialogue",
            version=version,
            agent_address=agent_address,
            nodes=[
                waiting_state,
                chatting_state,
                end_state,
            ],
            edges=[
                start_dialogue,
                cont_dialogue,
                end_dialogue,
            ],
        )
