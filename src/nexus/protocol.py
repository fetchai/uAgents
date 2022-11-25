import functools
import hashlib
from typing import Set, Optional, Union

from apispec import APISpec

from nexus.context import IntervalCallback, MessageCallback
from nexus.models import Model


OPENAPI_VERSION = "3.0.2"


class Protocol:
    def __init__(self, name: Optional[str] = None, version: Optional[str] = None):
        self._intervals = []
        self._interval_messages = {}
        self._message_handlers = {}
        self._models = {}
        self._replies = {}
        self._name = name or ""
        self._version = version or "0.1.0"
        self._canonical_name = f"{self._name}:{self._version}"
        self._digest = ""

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

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def canonical_name(self):
        return self._canonical_name

    @property
    def digest(self):
        assert self._digest != "", "Protocol digest empty"
        return self._digest

    def on_interval(
        self, period: float, messages: Optional[Union[Model, Set[Model]]] = None
    ):
        def decorator_on_interval(func: IntervalCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self.add_interval_handler(period, func, messages)

            return handler

        return decorator_on_interval

    def add_interval_handler(
        self,
        period: float,
        func: IntervalCallback,
        messages: Optional[Union[Model, Set[Model]]],
    ):

        # store the interval handler for later
        self._intervals.append((func, period))
        if messages is not None:
            if not isinstance(messages, set):
                messages = {messages}
            for message in messages:
                message_digest = Model.build_schema_digest(message)
                self._interval_messages[message_digest] = message

                self.spec.path(path=message.__name__, operations=message.dict())
        self._update_schema_digest()

    def on_message(
        self, model: Model, replies: Optional[Union[Model, Set[Model]]] = None
    ):
        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self.add_message_handler(model, func, replies)

            return handler

        return decorator_on_message

    def add_message_handler(
        self,
        model: Model,
        func: MessageCallback,
        replies: Optional[Union[Model, Set[Model]]],
    ):
        model_digest = Model.build_schema_digest(model)

        # update the model database
        self._models[model_digest] = model
        self._message_handlers[model_digest] = func
        if replies is not None:
            if not isinstance(replies, set):
                replies = {replies}
            self._replies[model_digest] = {
                Model.build_schema_digest(reply): reply for reply in replies
            }

            self.spec.path(
                path=model.__name__,
                operations=dict(
                    post=dict(replies=[reply.__name__ for reply in replies])
                ),
            )
        self._update_schema_digest()

    def _update_schema_digest(self):
        all_models = self._models | self._interval_messages
        sorted_schema_digests = sorted(list(all_models.keys()))
        hasher = hashlib.sha256()
        for digest in sorted_schema_digests:
            hasher.update(bytes.fromhex(digest))
        self._digest = hasher.digest().hex()
