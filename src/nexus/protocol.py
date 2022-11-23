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
        self._message_handlers = {}
        self._models = {}
        self._replies = {}
        self._name = name or ""
        self._version = version or "0.1.0"
        self._id = f"{self._name}:{self._version}"
        self._schema_digest = ""

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
    def id(self):  # pylint: disable=C0103
        return self._id

    @property
    def schema_digest(self):
        return self._schema_digest

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

            self.add_message_handler(model, func, replies)

            return handler

        return decorator_on_message

    def add_message_handler(
        self, model: Model, func: MessageCallback, replies: Union[Model, Set[Model]]
    ):
        schema_digest = Model.build_schema_digest(model)

        # update the model database
        self._models[schema_digest] = model
        self._message_handlers[schema_digest] = func
        if replies is not None:
            if not isinstance(replies, set):
                replies = {replies}
            self._replies[schema_digest] = {
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
        sorted_schema_digests = sorted(list(self._models.keys()))
        hasher = hashlib.sha256()
        for digest in sorted_schema_digests:
            hasher.update(bytes.fromhex(digest))
        self._schema_digest = hasher.digest().hex()
