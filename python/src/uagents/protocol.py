"""Exchange Protocol"""

import functools
from collections.abc import Awaitable, Callable
from logging import Logger
from typing import Any

from typing_extensions import deprecated
from uagents_core.models import Model
from uagents_core.protocol import ProtocolSpecification

from uagents.config import get_logger
from uagents.types import IntervalCallback, MessageCallback

logger: Logger = get_logger("protocol")


class Protocol:
    """
    The Protocol class encapsulates a particular set of functionalities for an agent.
    It typically relates to the exchange of messages between agents for executing some task.
    It includes the message (model) types it supports, the allowed replies, and the
    interval message handlers that define the logic of the protocol.
    """

    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        spec: ProtocolSpecification | None = None,
        role: str | None = None,
    ) -> None:
        """
        Initialize a Protocol instance.

        Args:
            name (str | None): The name of the protocol. Defaults to None.
            version (str | None): The version of the protocol. Defaults to None.
            spec (ProtocolSpecification | None): The protocol specification. Defaults to None.
            role (str | None): The role that the protocol will implement. Defaults to None.
        """
        self._interval_handlers: list[tuple[IntervalCallback, float]] = []
        self._interval_messages: set[str] = set()
        self._signed_message_handlers: dict[str, MessageCallback] = {}
        self._unsigned_message_handlers: dict[str, MessageCallback] = {}
        self._models: dict[str, type[Model]] = {}
        self._replies: dict[str, dict[str, type[Model]]] = {}
        self._digest = ""
        self._role: str | None = None
        self._locked = False

        if spec:
            self._init_from_spec(spec, role, name, version)
        else:
            self._spec = ProtocolSpecification(
                name=name or "", version=version or "0.1.0", interactions={}
            )

    @property
    def intervals(self) -> list[tuple[IntervalCallback, float]]:
        """
        Property to access the interval handlers.

        Returns:
            list[tuple[IntervalCallback, float]]: List of interval handlers and their periods.
        """
        return self._interval_handlers

    @property
    def models(self) -> dict[str, type[Model]]:
        """
        Property to access the registered models.

        Returns:
            dict[str, type[Model]]: Dictionary of registered models with schema digests as keys.
        """
        return self._models

    @property
    def replies(self) -> dict[str, dict[str, type[Model]]]:
        """
        Property to access the registered replies.

        Returns:
            dict[str, dict[str, type[Model]]]: Dictionary mapping message schema digests to their
            allowed replies.
        """
        return self._replies

    @property
    def interval_messages(self) -> set[str]:
        """
        Property to access the interval message digests.

        Returns:
            set[str]: Set of message digests that may be sent by interval handlers.
        """
        return self._interval_messages

    @property
    def signed_message_handlers(self) -> dict[str, MessageCallback]:
        """
        Property to access the signed message handlers.

        Returns:
            dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.
        """
        return self._signed_message_handlers

    @property
    def unsigned_message_handlers(self) -> dict[str, MessageCallback]:
        """
        Property to access the unsigned message handlers.

        Returns:
            dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.
        """
        return self._unsigned_message_handlers

    @property
    def name(self) -> str:
        """
        Property to access the protocol name.

        Returns:
            str: The protocol name.
        """
        return self._spec.name

    @property
    def version(self) -> str:
        """
        Property to access the protocol version.

        Returns:
            str: The protocol version.
        """
        return self._spec.version

    @property
    def canonical_name(self) -> str:
        """
        Property to access the canonical name of the protocol ('name:version').

        Returns:
            str: The canonical name of the protocol.
        """
        return f"{self.name}:{self.version}"

    @property
    def digest(self) -> str:
        """
        Property to access the digest of the protocol's manifest.

        Returns:
            str: The digest of the protocol's manifest.
        """
        return self.manifest()["metadata"]["digest"]

    @property
    def spec(self) -> ProtocolSpecification:
        """
        Property to access the protocol specification.

        Returns:
            ProtocolSpecification: The protocol specification.
        """
        return self._spec

    def _init_from_spec(
        self,
        spec: ProtocolSpecification,
        role: str | None,
        name: str | None,
        version: str | None,
    ) -> None:
        """
        Initialize the protocol interactions from a specification.

        Args:
            spec (ProtocolSpecification): The protocol specification.
            role (str | None): The role that the protocol will implement.
            name (str | None): The name of the protocol.
            version (str | None): The version of the protocol.
        """
        if name and spec.name and name != spec.name:
            logger.warning(
                f"Protocol specification name '{spec.name}' overrides given protocol name '{name}'"
            )
        if version and spec.version and version != spec.version:
            logger.warning(
                f"Protocol specification version '{spec.version}' "
                f"overrides given protocol version '{version}'"
            )
        spec.name = spec.name or name or ""
        spec.version = spec.version or version or "0.1.0"

        if spec.roles:
            if role is None:
                raise ValueError("Role must be specified for a protocol with roles")
            if role not in spec.roles:
                raise ValueError(f"Role '{role}' not found in protocol roles")
            self._role = role
            interactions = {
                model: replies
                for model, replies in spec.interactions.items()
                if model in spec.roles[role]
            }
        else:
            interactions = spec.interactions

        for model, replies in interactions.items():
            self._add_interaction(model, replies)

        self._spec = spec
        self._locked = True

    def _add_interaction(
        self, model: type[Model], replies: set[type[Model]] | None = None
    ) -> None:
        """
        Add a message model to the protocol along with replies if specified.

        Args:
            model (type[Model]): The message model type.
            replies (set[type[Model]] | None): The associated reply types. Defaults to None.
        """
        model_digest = Model.build_schema_digest(model)
        self._models[model_digest] = model

        if replies is not None:
            self.replies[model_digest] = {
                Model.build_schema_digest(reply): reply for reply in replies
            }

    def on_interval(
        self,
        period: float,
        messages: type[Model] | set[type[Model]] | None = None,
    ) -> Callable:
        """
        Decorator to register an interval handler for the protocol.

        Args:
            period (float): The interval period in seconds.
            messages (type[Model] | set[type[Model]] | None): The associated message types.

        Returns:
            Callable: The decorator to register the interval handler.
        """

        def decorator_on_interval(func: IntervalCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs) -> Awaitable[None]:
                return func(*args, **kwargs)

            self._add_interval_handler(period, func, messages)

            return handler

        return decorator_on_interval

    def _add_interval_handler(
        self,
        period: float,
        func: IntervalCallback,
        messages: type[Model] | set[type[Model]] | None,
    ) -> None:
        """
        Add an interval handler to the protocol.

        Args:
            period (float): The interval period in seconds.
            func (IntervalCallback): The interval handler function.
            messages (type[Model] | set[type[Model]] | None): The associated message types.
        """
        # store the interval handler for later
        self._interval_handlers.append((func, period))

        # if message types are specified, store these for validation
        if messages is not None:
            if not isinstance(messages, set):
                messages = {messages}
            for message in messages:
                message_digest = Model.build_schema_digest(message)
                self._interval_messages.add(message_digest)

    @deprecated(
        "on_query is deprecated and will be removed in a future release, use on_rest instead."
    )
    def on_query(
        self,
        model: type[Model],
        replies: type[Model] | set[type[Model]] | None = None,
    ) -> Callable:
        """
        Decorator to register a query handler for the protocol.

        Args:
            model (type[Model]): The message model type.
            replies (type[Model] | set[type[Model]] | None): The associated reply types.

        Returns:
            Callable: The decorator to register the query handler.
        """
        return self.on_message(model, replies, allow_unverified=True)

    def on_message(
        self,
        model: type[Model],
        replies: type[Model] | set[type[Model]] | None = None,
        allow_unverified: bool = False,
    ) -> Callable:
        """
        Decorator to register a message handler for the protocol.

        Args:
            model (type[Model]): The message model type.
            replies (type[Model] | set[type[Model]] | None): The associated reply types.
            allow_unverified (bool, optional): Whether to allow unverified messages.

        Returns:
            Callable: The decorator to register the message handler.
        """
        if self._locked:
            if model not in self._models.values():
                raise ValueError(
                    f"Cannot add interaction '{model.__name__}' "
                    f"to locked protocol {self.canonical_name}"
                )
            model_digest = Model.build_schema_digest(model)
            if replies is not None and replies != self._replies.get(model_digest):
                raise ValueError(
                    f"Specified replies for '{model.__name__}' ({replies}) "
                    f"do not match the replies defined in the protocol specification "
                    f"for {self.canonical_name}: {self._replies.get(model_digest)}"
                )

        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._add_message_handler(model, func, replies, allow_unverified)

            return handler

        return decorator_on_message

    def _add_message_handler(
        self,
        model: type[Model],
        func: MessageCallback,
        replies: type[Model] | set[type[Model]] | None,
        allow_unverified: bool = False,
    ):
        """
        Add a message handler to the protocol.

        Args:
            model (type[Model]): The message model type.
            func (MessageCallback): The message handler function.
            replies (type[Model] | set[type[Model]] | None): The associated reply types.
            allow_unverified (bool, optional): Whether to allow unverified messages.
        """
        model_digest = Model.build_schema_digest(model)

        # update the model database
        self._models[model_digest] = model
        if allow_unverified:
            self._unsigned_message_handlers[model_digest] = func
        else:
            self._signed_message_handlers[model_digest] = func
        if replies is None:
            replies = set()
        if not isinstance(replies, set):
            replies = {replies}
        if not self._locked:
            self._spec.interactions[model] = replies
        self._replies[model_digest] = {
            Model.build_schema_digest(reply): reply for reply in replies
        }

    def manifest(self) -> dict[str, Any]:
        """
        Generate the protocol's manifest, a long-form machine readable description of the
        protocol details and interface.

        Returns:
            dict[str, Any]: The protocol's manifest.
        """
        return self._spec.manifest(role=self._role)

    def verify(self) -> bool:
        """
        Check if the protocol implements all interactions of its specification.

        Returns:
            bool: True if the protocol implements the role, False otherwise.
        """
        if not self._locked:
            # No specification to verify against
            return True

        message_handlers: dict[str, MessageCallback] = (
            self._signed_message_handlers | self._unsigned_message_handlers
        )

        result = True
        # verify that all models required by the role are implemented
        for digest, model in self._models.items():
            if digest not in message_handlers:
                logger.error(
                    f"Protocol {self.canonical_name} does not implement "
                    f"a handler for the model '{model.__name__}'"
                    + f" required for the role '{self._role}'"
                    if self._role
                    else ""
                )
                result = False

        return result

    @staticmethod
    def compute_digest(manifest: dict[str, Any]) -> str:
        """
        Compute the digest of a given manifest.

        Args:
            manifest (dict[str, Any]): The manifest to compute the digest for.

        Returns:
            str: The computed digest.
        """
        return ProtocolSpecification.compute_digest(manifest)
