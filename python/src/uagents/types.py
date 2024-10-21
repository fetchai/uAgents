import hashlib
import json
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
)

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from uagents.crypto import Identity
from uagents.models import Model

if TYPE_CHECKING:
    from uagents.context import Context

JsonStr = str

IntervalCallback = Callable[["Context"], Awaitable[None]]
MessageCallback = Callable[["Context", str, Any], Awaitable[None]]
EventCallback = Callable[["Context"], Awaitable[None]]
WalletMessageCallback = Callable[["Context", Any], Awaitable[None]]

RestReturnType = Union[Dict[str, Any], Model]
RestGetHandler = Callable[["Context"], Awaitable[Optional[RestReturnType]]]
RestPostHandler = Callable[["Context", Any], Awaitable[Optional[RestReturnType]]]
RestHandler = Union[RestGetHandler, RestPostHandler]
RestMethod = Literal["GET", "POST"]
RestHandlerMap = Dict[Tuple[RestMethod, str], RestHandler]


class AgentEndpoint(BaseModel):
    url: str
    weight: int


class AgentInfo(BaseModel):
    agent_address: str
    endpoints: List[AgentEndpoint]
    protocols: List[str]


class RestHandlerDetails(BaseModel):
    method: RestMethod
    endpoint: str
    request_model: Optional[Type[Model]] = None
    response_model: Type[Union[Model, BaseModel]]


class AgentGeolocation(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False)
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    radius: Annotated[float, Field(ge=0)] = 0

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

    geolocation: Optional[AgentGeolocation] = None


class DeliveryStatus(str, Enum):
    """Delivery status of a message."""

    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass
class MsgDigest:
    """
    Represents a message digest containing a message and its schema digest.

    Attributes:
        message (Any): The message content.
        schema_digest (str): The schema digest of the message.
    """

    message: Any
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
        session (Optional[uuid.UUID]): The session ID of the message.
    """

    status: DeliveryStatus
    detail: str
    destination: str
    endpoint: str
    session: Optional[uuid.UUID] = None


class VerifiableModel(BaseModel):
    agent_address: str
    signature: Optional[str] = None

    def sign(self, identity: Identity):
        digest = self._build_digest()
        self.signature = identity.sign_digest(digest)

    def verify(self) -> bool:
        return self.signature is not None and Identity.verify_digest(
            self.agent_address, self._build_digest(), self.signature
        )

    def _build_digest(self) -> bytes:
        sha256 = hashlib.sha256()
        sha256.update(
            json.dumps(
                self.model_dump(exclude={"signature"}),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        return sha256.digest()


class AgentRegistrationAttestation(VerifiableModel):
    protocols: List[str]
    endpoints: List[AgentEndpoint]
    metadata: Optional[Dict[str, Union[str, Dict[str, str]]]] = None

    @field_serializer("protocols")
    def sort_protocols(self, val: List[str]) -> List[str]:
        return sorted(val)

    @field_serializer("endpoints")
    def sort_endpoints(self, val: List[AgentEndpoint]) -> List[AgentEndpoint]:
        return sorted(val, key=lambda x: x.url)


class AgentStatusUpdate(VerifiableModel):
    is_active: bool
