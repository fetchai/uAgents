import functools

from nexus.context import IntervalCallback, MessageCallback
from nexus.models import Model


class Protocol:
    def __init__(self):
        self._intervals = []
        self._message_handlers = {}
        self._models = {}

    @property
    def intervals(self):
        return self._intervals

    @property
    def models(self):
        return self._models

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

    def on_message(self, model: Model):
        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            schema_digest = Model.build_schema_digest(model)

            # update the model database
            self._models[schema_digest] = model
            self._message_handlers[schema_digest] = func

            return handler

        return decorator_on_message
