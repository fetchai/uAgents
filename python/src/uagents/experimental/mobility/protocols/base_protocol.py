from datetime import datetime
from typing import Any, Literal, Optional

from pydantic.v1 import confloat

from uagents import Context, Model, Protocol

PROTOCOL_NAME = "basic-mobility-handshake"
PROTOCOL_VERSION = "0.1.0"


class Location(Model):
    latitude: confloat(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: confloat(strict=True, ge=-180, le=180, allow_inf_nan=False)
    radius: confloat(
        gt=0, allow_inf_nan=False
    )  # This is used for compatibility with uagents message model


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
    supported_protocols: Optional[list[str]] = None


class CheckInResponse(Model):
    """Information to return after receiving a check-in message"""

    # the type of the responding agent (e.g., sign or traffic light)
    mobility_type: MobilityType
    # the signal of the entity represented by the agent (e.g., speed limit: 30, or "red")
    signal: str = ""
    # a human readable description of the entity that could be displayed on a gui
    description: str = ""
    # the mobility related protocols this agent supports
    supported_protocols: Optional[list[str]] = None


class CheckOut(Model):
    """Signal message to optionally send when leaving the service area of an agent"""


class CheckOutResponse(Model):
    """
    Checkout response to optionally include a summary regarding the "stay" in the service area
    """

    receipt: Optional[dict[str, Any]] = None


class StatusUpdate(Model):
    """Message to signal an update to all checked in mobility agents"""

    # the signal of the entity represented by the agent (e.g., speed limit: 30, or "red")
    signal: str = ""
    # the new location if changed
    new_location: Location | None = None


class StatusUpdateResponse(Model):
    """Optional response to return on a StatusUpdate"""

    text: str = ""


# pagination?
class MobilityLogRequest(Model):
    """Request the full agent log"""


class MobilityAgentLog(Model):
    """A log entry for a mobility agent"""

    timestamp: datetime
    active_address: str
    passive_address: str
    active_mobility_type: MobilityType
    passive_mobility_type: MobilityType
    interaction: Literal["checkin", "checkout"]

    # optional additional information
    additional_info: Optional[dict[str, Any]] = None


class MobilityAgentLogs(Model):
    """Response to a mobility log request"""

    logs: list[MobilityAgentLog]


mobility_base_protocol = Protocol(name=PROTOCOL_NAME, version=PROTOCOL_VERSION)


@mobility_base_protocol.on_message(MobilityLogRequest, replies=MobilityAgentLogs)
async def handle_log_request(ctx: Context, sender: str, _msg: MobilityLogRequest):
    logs = ctx.storage.get("mobility_logs") or []
    await ctx.send(sender, MobilityAgentLogs(logs=logs))
