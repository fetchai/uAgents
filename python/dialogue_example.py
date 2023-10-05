from uuid import UUID
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
        name: str | None = None,
        version: str | None = None,
        dialogue_id: UUID | None = None,
    ) -> None:
        rules = {
            ResourceQuery: [ResourceAvailability],
            ResourceAvailability: [ResourceReservation, ResourceRejection],
            ResourceReservation: [ResourceReservationConfirmation],
            ResourceRejection: [],
            ResourceReservationConfirmation: [],
        }  # predefine structure and enable passing specific messages into it
        starter = ResourceQuery
        ender = {ResourceRejection, ResourceReservationConfirmation}
        super().__init__(name, version, rules, dialogue_id, starter, ender)
