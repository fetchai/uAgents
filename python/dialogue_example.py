from src.uagents.contrib.dialogues import dialogue
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
            dialogue_id=None,
            agent_address=agent_address,
        )
