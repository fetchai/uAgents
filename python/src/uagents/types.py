import uuid
from collections.abc import Awaitable, Callable
from enum import Enum
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)
from typing_extensions import Self
from uagents_core.envelope import Envelope
from uagents_core.models import Model
from uagents_core.types import AddressPrefix, AgentEndpoint

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


class MsgInfo(BaseModel):
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


class MsgStatus(BaseModel):
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


class EnvelopeHistoryEntry(BaseModel):
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    version: int
    sender: str
    target: str
    session: UUID4
    schema_digest: str
    protocol_digest: str | None = None
    payload: str | None = None

    @field_serializer("session")
    def serialize_session(self, session: UUID4, _info) -> JsonStr:
        return str(session)

    @classmethod
    def from_envelope(cls, envelope: Envelope) -> Self:
        return cls(
            version=envelope.version,
            sender=envelope.sender,
            target=envelope.target,
            session=envelope.session,
            schema_digest=envelope.schema_digest,
            protocol_digest=envelope.protocol_digest,
            payload=envelope.decode_payload(),
        )


class EnvelopeHistory(BaseModel):
    envelopes: list[EnvelopeHistoryEntry]

    def add_entry(self, entry: EnvelopeHistoryEntry) -> None:
        self.envelopes.append(entry)
        self.apply_retention_policy()

    def apply_retention_policy(self) -> None:
        """Remove entries older than 24 hours"""
        cutoff_time = time.time() - 86400
        for e in self.envelopes:
            if e.timestamp < cutoff_time:
                self.envelopes.remove(e)
            else:
                break
