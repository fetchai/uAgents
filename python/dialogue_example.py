from src.uagents.experimental.dialogues import dialogue
from uagents import Model


class ResourceQuery(Model):
    pass


class ResourceAvailability(Model):
    qty: int


class ResourceRejection(Model):
    pass


class ResourceReservation(Model):
    qty: int


class ResourceReservationConfirmation(Model):
    pass


class ResourceRequestDialogue(dialogue.Dialogue):
    def __init__(
        self,
        version: str | None = None,
        agent_address: str | None = None,
    ) -> None:
        rules = {
            ResourceQuery: {ResourceAvailability},
            ResourceAvailability: {ResourceReservation, ResourceRejection},
            ResourceReservation: {ResourceReservationConfirmation},
            ResourceRejection: {},
            ResourceReservationConfirmation: {},
        }  # predefine structure and enable passing specific messages into it
        super().__init__(
            name="ResourceRequestDialogue",
            version=version,
            rules=rules,
            agent_address=agent_address,
        )


# This is a specific derivation of the abstract dialogue class
# The rules will be predefined and the actual messages will be passed into it
class A_ResourceRequestDialogue(dialogue.AbstractDialogue):
    """Pattern definition"""

    state1 = dialogue.Node(
        name="Dialogue Creation",
        description="This is the initial state of the dialogue.",
    )
    state2 = dialogue.Node(
        name="Requested",
        description="This is the state after the resource has been requested.",
    )
    state3 = dialogue.Node(
        name="Offer Received",
        description="This is the state after the resource has been offered.",
    )

    # Models are attached to the transitions, this way we may be able to
    # predefine a specific message structure that can also be overwritten
    transition1 = dialogue.Edge(
        name="Resource Query",
        description="This is the transition from state1 to state2. etc.",
        parent=state1,
        child=state2,
    )
    transition2 = dialogue.Edge(
        name="Resource Availability",
        description="This is the description of the transition etc.",
        parent=state2,
        child=state3,
    )

    def __init__(
        self,
        version: str | None = None,
        agent_address: str | None = None,
    ) -> None:
        super().__init__(  # pylint: disable=unexpected-keyword-arg
            name="ResourceRequestDialogue_a",
            version=version,
            agent_address=agent_address,
            nodes=[self.state1, self.state2, self.state3, ...],
            edges=[self.transition1, self.transition2, ...],
        )
