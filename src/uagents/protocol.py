import functools
import hashlib
from typing import Dict, List, Optional, Set, Tuple, Union

from apispec import APISpec

from uagents.context import IntervalCallback, MessageCallback
from uagents.models import Model


OPENAPI_VERSION = "3.0.2"


class Protocol:
    def __init__(self, name: Optional[str] = None, version: Optional[str] = None):
        self._intervals: List[Tuple[IntervalCallback, float]] = []
        self._interval_messages: Set[str] = set()
        self._signed_message_handlers: Dict[str, MessageCallback] = {}
        self._unsigned_message_handlers: Dict[str, MessageCallback] = {}
        self._models: Dict[str, Model] = {}
        self._replies: Dict[str, Set[Model]] = {}
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
    def interval_messages(self):
        return self._interval_messages

    @property
    def signed_message_handlers(self):
        return self._signed_message_handlers

    @property
    def unsigned_message_handlers(self):
        return self._unsigned_message_handlers

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
        return self._digest

    def on_interval(
        self, period: float, messages: Optional[Union[Model, Set[Model]]] = None
    ):
        def decorator_on_interval(func: IntervalCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._add_interval_handler(period, func, messages)

            return handler

        return decorator_on_interval

    def _add_interval_handler(
        self,
        period: float,
        func: IntervalCallback,
        messages: Optional[Union[Model, Set[Model]]],
    ):

        # store the interval handler for later
        self._intervals.append((func, period))

        # if message types are specified, store these for validation
        if messages is not None:
            if not isinstance(messages, set):
                messages = {messages}
            for message in messages:
                message_digest = Model.build_schema_digest(message)
                self._interval_messages.add(message_digest)

                self.spec.path(path=message.__name__, operations={})
        self._update_digest()

    def on_query(
        self,
        model: Model,
        replies: Optional[Union[Model, Set[Model]]] = None,
    ):
        return self.on_message(model, replies, allow_unverified=True)

    def on_message(
        self,
        model: Model,
        replies: Optional[Union[Model, Set[Model]]] = None,
        allow_unverified: Optional[bool] = False,
    ):
        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._add_message_handler(model, func, replies, allow_unverified)

            return handler

        return decorator_on_message

    def _add_message_handler(
        self,
        model: Model,
        func: MessageCallback,
        replies: Optional[Union[Model, Set[Model]]],
        allow_unverified: Optional[bool] = False,
    ):
        model_digest = Model.build_schema_digest(model)

        # update the model database
        self._models[model_digest] = model
        if allow_unverified:
            self._unsigned_message_handlers[model_digest] = func
        else:
            self._signed_message_handlers[model_digest] = func
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
        self._update_digest()

    def _update_digest(self):
        all_model_digests = set(self._models.keys()) | self._interval_messages
        sorted_schema_digests = sorted(list(all_model_digests))
        hasher = hashlib.sha256()
        for digest in sorted_schema_digests:
            hasher.update(bytes.fromhex(digest))
        self._digest = hasher.digest().hex()
