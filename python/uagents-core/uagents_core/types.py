import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

JsonStr = str

AgentType = Literal["uagent"] | str
AddressPrefix = Literal["agent", "test-agent"]


class AgentEndpoint(BaseModel):
    url: str
    weight: int


class AgentInfo(BaseModel):
    address: str
    endpoints: list[AgentEndpoint]
    protocols: list[str]
    agent_type: AgentType
    metadata: dict[str, Any] | None = None
    prefix: AddressPrefix | None = None
    port: int | None = None


class AgentRecord(BaseModel):
    address: str
    weight: float


class DomainRecord(BaseModel):
    name: str
    agents: list[AgentRecord]


class DomainStatus(Enum):
    Registered = "Registered"
    Pending = "Pending"
    Checking = "Checking"
    Updating = "Updating"
    Deleting = "Deleting"
    Failed = "Failed"


class Domain(BaseModel):
    name: str
    status: DomainStatus
    expiry: datetime | None = None
    assigned_agents: list[AgentRecord]


class DeliveryStatus(str, Enum):
    """Delivery status of a message."""

    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


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


class Resolver(ABC):
    @abstractmethod
    async def resolve(self, destination: str) -> tuple[str | None, list[str]]:
        """
        Resolve the destination to an address and endpoint.

        Args:
            destination (str): The destination name or address to resolve.

        Returns:
            tuple[str | None, list[str]]: The address (if available) and resolved endpoints.
        """
        raise NotImplementedError

    @abstractmethod
    def sync_resolve(self, destination: str) -> list[str]:
        """
        Resolve the destination to a list of endpoints.

        Args:
            destination (str): The destination name or address to resolve.

        Returns:
            list[str]: The resolved endpoints.
        """
        raise NotImplementedError


class AgentGeoLocationDetails(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    name: str | None = Field(default=None, description="the full agent location")
    description: str | None = Field(
        default=None, description="the description of the agent location"
    )
    latitude: float | None = Field(
        default=None, description="the latitude of the agent location"
    )
    longitude: float | None = Field(
        default=None, description="the longitude of the agent location"
    )
    street: str | None = Field(
        default=None, description="the street where the agent is located"
    )
    city: str | None = Field(
        default=None, description="the city where the agent is located"
    )
    state: str | None = Field(
        default=None, description="the state where the agent is located"
    )
    postal_code: str | None = Field(
        default=None, description="the postal code where the agent is located"
    )
    country: str | None = Field(
        default=None, description="the country where the agent is located"
    )
    url: str | None = Field(
        default=None, description="the url belonging to the agent location"
    )
    image_url: str | None = Field(
        default=None, description="the image url belonging to the agent location"
    )


class AgentGeolocation(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False, extra="forbid")
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

    geolocation: AgentGeolocation | AgentGeoLocationDetails | None = None
