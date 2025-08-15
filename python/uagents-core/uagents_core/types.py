import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel

JsonStr = str

AgentType = Literal["mailbox", "proxy", "custom"]
AddressPrefix = Literal["agent", "test-agent"]


class AgentEndpoint(BaseModel):
    url: str
    weight: int


class AgentInfo(BaseModel):
    address: str
    prefix: AddressPrefix
    endpoints: list[AgentEndpoint]
    protocols: list[str]
    metadata: dict[str, Any] | None = None
    agent_type: AgentType
    port: int | None = None


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
