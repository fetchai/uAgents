from pydantic import UUID4
from uagents import Model


class Proposal(Model):
    id: UUID4
    item: str
    price: float


class Reject(Model):
    proposal_id: UUID4
    reason: str


class CounterProposal(Model):
    proposal_id: UUID4
    item: str
    price: float


class Acceptance(Model):
    proposal_id: UUID4
    item: str
    price: float
