from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
)

from pydantic import BaseModel

from uagents.context import Context
from uagents.models import Model

RestReturnType = Union[Dict[str, Any], Model]
RestGetHandler = Callable[[Context], Awaitable[Optional[RestReturnType]]]
RestPostHandler = Callable[[Context, Any], Awaitable[Optional[RestReturnType]]]
RestHandler = Union[RestGetHandler, RestPostHandler]
RestMethod = Literal["GET", "POST"]


class RestHandlerDetails(BaseModel):
    method: RestMethod
    handler: RestHandler
    request_model: Optional[Type[Model]] = None
    response_model: Type[Model]


RestHandlerMap = Dict[Tuple[RestMethod, str], RestHandlerDetails]
