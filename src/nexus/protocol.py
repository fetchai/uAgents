import functools
from typing import Set, Optional, Union

from apispec import APISpec

from nexus.context import IntervalCallback, MessageCallback
from nexus.models import Model


OPENAPI_VERSION = "3.0.2"


class Protocol:
    def __init__(self, name: Optional[str] = None, version: Optional[str] = None):
        self._intervals = []
        self._message_handlers = {}
        self._models = {}
        self._replies = {}
        self._name = name or ""
        self._version = version or "0.1.0"

        self.spec = APISpec(
            title=self._name,
            version=self._version,
            openapi_version=OPENAPI_VERSION,
        )

    @property
    def intervals(self):
        return self._intervals

    @property
    def models(self):
        return self._models

    @property
    def replies(self):
        return self._replies

    @property
    def message_handlers(self):
        return self._message_handlers

    def on_interval(self, period: float):
        def decorator_on_interval(func: IntervalCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            # store the interval handler for later
            self._intervals.append((func, period))

            return handler

        return decorator_on_interval

    def on_message(
        self, model: Model, replies: Optional[Union[Model, Set[Model]]] = None
    ):
        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._add_message_handler(model, func, replies)

            return handler

        return decorator_on_message

    def _add_message_handler(self, model, func, replies):
        schema_digest = Model.build_schema_digest(model)

        # update the model database
        self._models[schema_digest] = model
        self._message_handlers[schema_digest] = func
        if replies is not None:
            if not isinstance(replies, set):
                replies = {replies}
            self._replies[schema_digest] = {
                Model.build_schema_digest(reply) for reply in replies
            }

            self.spec.path(
                path=model.__name__,
                operations=dict(
                    post=dict(replies=[reply.__name__ for reply in replies])
                ),
            )
