from enum import Enum

from uagents_core.models import Model
from uagents_core.protocol import ProtocolSpecification


class TierType(str, Enum):
    FREE = "free"
    PLUS = "plus"
    PRO = "pro"


class Tier(Model):
    tier_id: str
    tier_type: TierType
    amount: str
    currency: str


class RequestAgentSubscriptionRenewal(Model):
    update_id: str
    tier: Tier


class RequestAgentSubscriptionUpgrade(Model):
    # the system generated event id associated with this upgrade
    update_id: str

    # the tier this upgrade is subscribing to
    new_subscription: Tier

    # previous subscription, None if it was the 'free' type
    existing_subscription: Tier | None = None


class AcceptAgentSubscriptionUpdate(Model):
    update_id: str


class RejectAgentSubscriptionUpdate(Model):
    update_id: str


subscription_protocol_spec = ProtocolSpecification(
    name="AgentSubscriptionProtocol",
    version="0.2.0",
    interactions={
        RequestAgentSubscriptionRenewal: {
            AcceptAgentSubscriptionUpdate,
            RejectAgentSubscriptionUpdate,
        },
        RequestAgentSubscriptionUpgrade: {
            AcceptAgentSubscriptionUpdate,
            RejectAgentSubscriptionUpdate,
        },
        AcceptAgentSubscriptionUpdate: set(),
        RejectAgentSubscriptionUpdate: set(),
    },
    roles={
        "requester": {AcceptAgentSubscriptionUpdate, RejectAgentSubscriptionUpdate},
        "agent": {RequestAgentSubscriptionRenewal, RequestAgentSubscriptionUpgrade},
    },
)
