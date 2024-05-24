"""Specific dialogue class for the Agentverse chit-chat dialogue."""

from typing import Type

from uagents import Model
from uagents.experimental.dialogues import Dialogue, Edge, Node


# This is the definition of the dialogue messages that can be exchanged
# each transition needs a separate message and since digests are calculated
# based on the message structure, the message classes should not be changed.
class InitiateChitChatDialogue(Model):
    pass


class ChitChatDialogueMessage(Model):
    text: str


class ConcludeChitChatDialogue(Model):
    pass


class AgentverseChitChat(Dialogue):
    """
    NOTE: Do not change this class as it is used in Agentverse and to be compatible
          both parties need to use the same dialogue implementation.

    The Agentverse compatible ChitChatDialogue is the first version of the generic
    Dialogue implementation that can be used by any agent to exchange messages
    with a hosted agent in Agentverse.

    It provides a simple pattern that allows 2 parties to exchange an arbitrary
    number of "ChitChat" messages.
    Messages are started with an initial message, followed by any number of
    "ChitChat" messages, and finally concluded with an end message.
    (see python/examples/17-stateful-communication/agent5.py for a usage example)
    """

    # Node definition for the dialogue states
    chatting_state_node = Node(
        name="Chit Chatting",
        description="While in this state, more messages can be exchanged.",
    )
    end_state_node = Node(
        name="Concluded",
        description="This is the state after the dialogue has been concluded and "
        "no more messages will be accepted.",
    )

    # Edge definition for the dialogue transitions
    start_dialogue_edge = Edge(
        name="Start Dialogue",
        description=(
            "A message that initiates a ChitChat conversation and provides "
            "any information needed to set the context and let the receiver "
            "decide whether to accept or directly end this conversation."
        ),
        parent=None,
        child=chatting_state_node,
    )
    cont_dialogue_edge = Edge(
        name="Continue Dialogue",
        description=(
            "A general message structure to exchange information without "
            "annotating further states or limiting the message flow in any way."
        ),
        parent=chatting_state_node,
        child=chatting_state_node,
    )
    end_dialogue_edge = Edge(
        name="End Dialogue",
        description=(
            "A final message that can be sent at any time by either party "
            "to finish this dialogue."
        ),
        parent=chatting_state_node,
        child=end_state_node,
    )

    def __init__(
        self,
        storage=None,
    ) -> None:
        """
        Initialize the simple ChitChatDialogue class.

        Args:
            version (Optional[str], optional): Version of the dialogue. Defaults to None.
            storage (Optional[StorageAPI], optional): Storage to use.
                None will generate a new KeyValueStore based on the dialogue name.
                Defaults to None.
        """
        super().__init__(
            name="ChitChatDialogue_simple",
            version="0.1.0",
            storage=storage,
            nodes=[
                self.chatting_state_node,
                self.end_state_node,
            ],
            edges=[
                self.start_dialogue_edge,
                self.cont_dialogue_edge,
                self.end_dialogue_edge,
            ],
        )

    def on_start_dialogue(self, model: Type[Model]):
        """
        This handler is triggered when the initial message of the
        dialogue is received.
        It automatically transitions into the chit-chatting state for
        the next message exchange or directly into the end state.
        """
        return super()._on_state_transition(self.start_dialogue_edge.name, model)

    def on_continue_dialogue(self, model: Type[Model]):
        """
        This handler is triggered for every incoming "chitchat" message
        once the session has been accepted.
        Any additional stateful information within a dialogue needs to be
        persisted explicitly to access it at a later point in the dialogue.
        """
        return super()._on_state_transition(self.cont_dialogue_edge.name, model)

    def on_end_session(self, model: Type[Model]):
        """
        This handler is triggered once the other party has ended the dialogue.
        Any final conclusion or cleanup goes here.
        """
        return super()._on_state_transition(self.end_dialogue_edge.name, model)
