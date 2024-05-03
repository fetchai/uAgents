from dataclasses import dataclass
from typing import Literal, Awaitable, Callable, Union, Tuple, Dict, Optional, Type

from uagents import Model, Context

RestGetHandler = Callable[[Context], Awaitable[Optional[Model]]]
RestPostHandler = Callable[[Context, Model], Awaitable[Optional[Model]]]
RestHandler = Union[RestGetHandler, RestPostHandler]
RestMethod = Union[Literal["GET"], Literal["POST"]]


@dataclass
class RestHandlerDetails:
    handler: RestHandler
    request_model: Optional[Type[Model]]
    response_model: Type[Model]


RestHandlerMap = Dict[Tuple[RestMethod, str], RestHandlerDetails]
