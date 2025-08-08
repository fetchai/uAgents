"""
This module contains the protocol specification for agent subscription management.

A chat agent that supports this protocol will be able to accept or reject paid
subscription requests from other agents.
"""

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
    # the system generated event id associated with this upgrade
    update_id: str

    # the tier this upgrade is subscribing to
    tier: Tier


class RequestAgentSubscriptionUpgrade(Model):
    # the system generated event id associated with this upgrade
    update_id: str

    # the tier this upgrade is subscribing to
    new_subscription: Tier

    # previous subscription, None if it was the 'free' type
    existing_subscription: Tier | None = None


class AcceptAgentSubscriptionUpdate(Model):
    # the update id associated with this upgrade
    update_id: str


class RejectAgentSubscriptionUpdate(Model):
    # the update id associated with this upgrade
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
