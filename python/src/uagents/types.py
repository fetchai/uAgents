import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from uagents_core.models import Model
from uagents_core.types import AgentEndpoint

if TYPE_CHECKING:
    from uagents.context import Context

JsonStr = str

IntervalCallback = Callable[["Context"], Awaitable[None]]
MessageCallback = Callable[["Context", str, Any], Awaitable[None]]
EventCallback = Callable[["Context"], Awaitable[None]]
WalletMessageCallback = Callable[["Context", Any], Awaitable[None]]

RestReturnType = dict[str, Any] | Model
RestGetHandler = Callable[["Context"], Awaitable[RestReturnType | None]]
RestPostHandler = Callable[["Context", Any], Awaitable[RestReturnType | None]]
RestHandler = RestGetHandler | RestPostHandler
RestMethod = Literal["GET", "POST"]
RestHandlerMap = dict[tuple[RestMethod, str], RestHandler]


AddressPrefix = Literal["agent", "test-agent"]
AgentNetwork = Literal["mainnet", "testnet"]


class AgentInfo(BaseModel):
    address: str
    prefix: AddressPrefix
    endpoints: list[AgentEndpoint]
    protocols: list[str]
    metadata: dict[str, Any] | None = None


class RestHandlerDetails(BaseModel):
    method: RestMethod
    endpoint: str
    request_model: type[Model] | None = None
    response_model: type[Model | BaseModel]


class AgentGeolocation(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False)
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    radius: Annotated[float, Field(gt=0)] = 0.5

    @field_validator("latitude", "longitude")
    @classmethod
    def serialize_precision(cls, val: float) -> float:
        """
        Round the latitude and longitude to 6 decimal places.
        Equivalent to 0.11m precision.
        """
        return round(val, 6)


class AgentMetadata(BaseModel):
    """
    Model used to validate metadata for an agent.

    Framework specific fields will be added here to ensure valid serialization.
    Additional fields will simply be passed through.
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )

    geolocation: AgentGeolocation | None = None


class DeliveryStatus(str, Enum):
    """Delivery status of a message."""

    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass
class MsgInfo:
    """
    Represents a message digest containing a message and its schema digest and sender.

    Attributes:
        message (Any): The message content.
        sender (str): The address of the sender of the message.
        schema_digest (str): The schema digest of the message.
    """

    message: Any
    sender: str
    schema_digest: str


@dataclass
class MsgStatus:
    """
    Represents the status of a sent message.

    Attributes:
        status (str): The delivery status of the message {'sent', 'delivered', 'failed'}.
        detail (str): The details of the message delivery.
        destination (str): The destination address of the message.
        endpoint (str): The endpoint the message was sent to.
        session (uuid.UUID | None): The session ID of the message.
    """

    status: DeliveryStatus
    detail: str
    destination: str
    endpoint: str
    session: uuid.UUID | None = None
