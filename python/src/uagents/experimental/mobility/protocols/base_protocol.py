from typing import Any, Literal

from pydantic.v1 import confloat

from uagents import Model, Protocol

PROTOCOL_NAME = "basic-mobility-handshake"
PROTOCOL_VERSION = "0.1.0"


# This is used for compatibility with uagents message model
class Location(Model):
    latitude: confloat(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: confloat(strict=True, ge=-180, le=180, allow_inf_nan=False)
    radius: confloat(gt=0, allow_inf_nan=False)


MobilityType = Literal[
    "traffic_signal",
    "traffic_sign",
    "speed_camera",
    "incident",  # collection for temporary situations
    "vehicle",
    "movable",  # collection for anything mobile except vehicles
    "zone",
]


class CheckIn(Model):
    """Signal message to send to an agent once entering its area of service"""

    # the type of the agent checking in (e.g., vehicle or pedestrian)
    mobility_type: MobilityType
    # the mobility related protocols this agent supports
    supported_protocols: list[str] | None = None


class CheckInResponse(Model):
    """Information to return after receiving a check-in message"""

    # the type of the responding agent (e.g., sign or traffic light)
    mobility_type: MobilityType
    # the signal of the entity represented by the agent (e.g., speed limit: 30, or "red")
    signal: str = ""
    # a human readable description of the entity that could be displayed on a gui
    description: str = ""
    # the mobility related protocols this agent supports
    supported_protocols: list[str] | None = None


class CheckOut(Model):
    """Signal message to optionally send when leaving the service area of an agent"""


class CheckOutResponse(Model):
    """
    Checkout response to optionally include a summary regarding the "stay" in the service area
    """

    receipt: dict[str, Any] | None = None


class StatusUpdate(Model):
    """Message to signal an update to all checked in mobility agents"""

    # the signal of the entity represented by the agent (e.g., speed limit: 30, or "red")
    signal: str = ""
    # the new location if changed
    new_location: Location | None = None


class StatusUpdateResponse(Model):
    """Optional response to return on a StatusUpdate"""

    text: str = ""


mobility_base_protocol = Protocol(name=PROTOCOL_NAME, version=PROTOCOL_VERSION)
