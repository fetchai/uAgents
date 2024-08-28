import uuid
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
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

from pydantic import BaseModel

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


class AgentInfo(BaseModel):
    agent_address: str
    endpoints: List
    protocols: List

class RestHandlerDetails(BaseModel):
    method: RestMethod
    endpoint: str
    request_model: Optional[Type[Model]] = None
    response_model: Type[Union[Model, BaseModel]]


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
