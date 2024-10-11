from typing import Any, Optional

from uagents import Model, Protocol

PROTOCOL_NAME = "basic-mobility-handshake"
PROTOCOL_VERSION = "0.1.0"


class CheckIn(Model):
    """Signal message to send to an agent once entering its area of service"""

    # the type of the agent checking in (e.g., vehicle or pedestrian)
    mobility_type: str
    # the mobility related protocols this agent supports
    supported_protocols: Optional[list[str]] = None


class CheckInResponse(Model):
    """Information to return after receiving a checkin message"""

    # the type of the responding agent (e.g., sign or traffic light) TODO
    mobility_type: str
    # the signal of the entity represented by the agent (e.g., speed lmit: 30, or "red")
    signal: str = ""
    # a human readable description of the entity that could be displayed on a gui
    description: str = ""
    # the mobility related protocols this agent supports
    supported_protocols: Optional[list[str]] = None


# > There may be more specific checkin responses for different types of agents
# class TrafficLightCheckIn(CheckInResponse):
#     """Traffic light specific checkin response"""

#     # the current signal of the traffic light
#     signal: str
#     # the time the signal was last changed
#     last_change: str


class CheckOut(Model):
    """Signal message to optionally send when leaving the serice area of an agent"""


class CheckOutResponse(Model):
    """
    Checkout response to optionally include a summary regarding the "stay" in the service area
    """

    receipt: Optional[dict[str, Any]] = None


mobility_base_protocol = Protocol(name=PROTOCOL_NAME, version=PROTOCOL_VERSION)
