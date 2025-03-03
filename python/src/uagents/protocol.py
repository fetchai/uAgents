"""Exchange Protocol"""

import copy
import functools
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from pydantic import BaseModel, ValidationInfo, field_validator

from uagents.config import get_logger
from uagents.models import Model
from uagents.types import IntervalCallback, MessageCallback

logger = get_logger("protocol")


class ProtocolSpecification(BaseModel):
    """
    Specification for the interactions and roles of a protocol.
    """

    interactions: Dict[Type[Model], Set[Type[Model]]]
    roles: Optional[Dict[str, Set[Type[Model]]]] = None
    version: Optional[str] = "1.0"

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, roles, info: ValidationInfo):
        """
        Ensure that all models included in roles are also included in the interactions.
        """
        if roles is None:
            return roles

        interactions: Dict[Type[Model], Set[Type[Model]]] = info.data["interactions"]
        interaction_models = set(interactions.keys())

        for role, models in roles.items():
            invalid_models = models - interaction_models
            if invalid_models:
                model_names = [model.__name__ for model in invalid_models]
                raise ValueError(
                    f"Role '{role}' contains models that don't "
                    f"exist in interactions: {model_names}"
                )
        return roles


class Protocol:
    """
    The Protocol class encapsulates a particular set of functionalities for an agent.
    It typically relates to the exchange of messages between agents for executing some task.
    It includes the message (model) types it supports, the allowed replies, and the
    interval message handlers that define the logic of the protocol.

    """

    def __init__(
        self,
        name: Optional[str] = None,
        version: Optional[str] = None,
        spec: Optional[ProtocolSpecification] = None,
        role: Optional[str] = None,
    ):
        """
        Initialize a Protocol instance.

        Args:
            name (Optional[str], optional): The name of the protocol. Defaults to None.
            version (Optional[str], optional): The version of the protocol. Defaults to None.
        """
        self._interval_handlers: List[Tuple[IntervalCallback, float]] = []
        self._interval_messages: Set[str] = set()
        self._signed_message_handlers: Dict[str, MessageCallback] = {}
        self._unsigned_message_handlers: Dict[str, MessageCallback] = {}
        self._models: Dict[str, Type[Model]] = {}
        self._replies: Dict[str, Dict[str, Type[Model]]] = {}
        self._name = name or ""
        self._version = version or "0.1.0"
        self._canonical_name = f"{self._name}:{self._version}"
        self._digest = ""
        self._interactions: Optional[Dict[Type[Model], Set[Type[Model]]]] = None
        self._role: Optional[str] = None
        self._locked = False

        if spec:
            self._init_from_spec(spec, role)

    @property
    def intervals(self):
        """
        Property to access the interval handlers.

        Returns:
            List[Tuple[IntervalCallback, float]]: List of interval handlers and their periods.
        """
        return self._interval_handlers

    @property
    def models(self):
        """
        Property to access the registered models.

        Returns:
            Dict[str, Type[Model]]: Dictionary of registered models with schema digests as keys.
        """
        return self._models

    @property
    def replies(self):
        """
        Property to access the registered replies.

        Returns:
            Dict[str, Dict[str, Type[Model]]]: Dictionary mapping message schema digests to their
            allowed replies.
        """
        return self._replies

    @property
    def interval_messages(self):
        """
        Property to access the interval message digests.

        Returns:
            Set[str]: Set of message digests that may be sent by interval handlers.
        """
        return self._interval_messages

    @property
    def signed_message_handlers(self):
        """
        Property to access the signed message handlers.

        Returns:
            Dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.
        """
        return self._signed_message_handlers

    @property
    def unsigned_message_handlers(self):
        """
        Property to access the unsigned message handlers.

        Returns:
            Dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.
        """
        return self._unsigned_message_handlers

    @property
    def name(self):
        """
        Property to access the protocol name.

        Returns:
            str: The protocol name.
        """
        return self._name

    @property
    def version(self):
        """
        Property to access the protocol version.

        Returns:
            str: The protocol version.
        """
        return self._version

    @property
    def canonical_name(self):
        """
        Property to access the canonical name of the protocol ('name:version').

        Returns:
            str: The canonical name of the protocol.
        """
        return self._canonical_name

    @property
    def digest(self):
        """
        Property to access the digest of the protocol's manifest.

        Returns:
            str: The digest of the protocol's manifest.
        """
        return self.manifest()["metadata"]["digest"]

    def _init_from_spec(self, spec: ProtocolSpecification, role: Optional[str] = None):
        """
        Initialize the protocol interactions from a specification.

        Args:
            spec (ProtocolSpecification): The protocol specification.
            role (Optional[str], optional): The role that the protocol will implement.
        """
        if spec.roles:
            if role is None:
                raise ValueError("Role must be specified for a protocol with roles")
            if role not in spec.roles:
                raise ValueError(f"Role '{role}' not found in protocol roles")
            self._role = role
            self._interactions = {
                model: replies
                for model, replies in spec.interactions.items()
                if model in spec.roles[role]
            }
        else:
            self._interactions = spec.interactions

        for model, replies in self._interactions.items():
            self._add_interaction(model, replies)

        self._locked = True

    def _add_interaction(
        self, model: Type[Model], replies: Optional[Set[Type[Model]]] = None
    ):
        """
        Add a message model to the protocol along with replies if specified.

        Args:
            model (Type[Model]): The message model type.
            replies (Optional[Union[Type[Model], Set[Type[Model]]], optional): The associated
            reply types. Defaults to None.
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
        messages: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
    ):
        """
        Decorator to register an interval handler for the protocol.

        Args:
            period (float): The interval period in seconds.
            messages (Optional[Union[Type[Model], Set[Type[Model]]]], optional): The associated
            message types. Defaults to None.

        Returns:
            Callable: The decorator to register the interval handler.
        """

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
        messages: Optional[Union[Type[Model], Set[Type[Model]]]],
    ):
        """
        Add an interval handler to the protocol.

        Args:
            period (float): The interval period in seconds.
            func (IntervalCallback): The interval handler function.
            messages (Optional[Union[Type[Model], Set[Type[Model]]]]): The associated message types.
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

    def on_query(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
    ):
        """
        Decorator to register a query handler for the protocol.

        Args:
            model (Type[Model]): The message model type.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]], optional): The associated
            reply types. Defaults to None.

        Returns:
            Callable: The decorator to register the query handler.
        """
        return self.on_message(model, replies, allow_unverified=True)

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
    ):
        """
        Decorator to register a message handler for the protocol.

        Args:
            model (Type[Model]): The message model type.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]], optional): The associated
            reply types. Defaults to None.
            allow_unverified (Optional[bool], optional): Whether to allow unverified messages.
            Defaults to False.

        Returns:
            Callable: The decorator to register the message handler.
        """
        if self._locked and model not in self._models.values():
            raise ValueError(
                f"Cannot add interaction '{model.__name__}' "
                f"to locked protocol {self.canonical_name}"
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
        model: Type[Model],
        func: MessageCallback,
        replies: Optional[Union[Type[Model], Set[Type[Model]]]],
        allow_unverified: Optional[bool] = False,
    ):
        """
        Add a message handler to the protocol.

        Args:
            model (Type[Model]): The message model type.
            func (MessageCallback): The message handler function.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]]): The associated reply types.
            allow_unverified (Optional[bool], optional): Whether to allow unverified messages.
            Defaults to False.
        """
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

    def manifest(self) -> Dict[str, Any]:
        """
        Generate the protocol's manifest, a long-form machine readable description of the
        protocol details and interface.

        Returns:
            Dict[str, Any]: The protocol's manifest.
        """
        metadata = {
            "name": self._name,
            "version": self._version,
        }

        manifest = {
            "version": "1.0",
            "metadata": {},
            "models": [],
            "interactions": [],
        }

        all_models: Dict[str, Type[Model]] = {}

        for schema_digest, model in self._models.items():
            if schema_digest not in all_models:
                all_models[schema_digest] = model

        for _, replies in self._replies.items():
            for schema_digest, model in replies.items():
                if schema_digest not in all_models:
                    all_models[schema_digest] = model

        for schema_digest, model in all_models.items():
            manifest["models"].append(
                {"digest": schema_digest, "schema": model.schema()}
            )

        for request, responses in self._replies.items():
            manifest["interactions"].append(
                {
                    "type": "query"
                    if request in self._unsigned_message_handlers
                    else "normal",
                    "request": request,
                    "responses": sorted(list(responses.keys())),
                }
            )

        encoded = json.dumps(manifest, indent=None, sort_keys=True).encode("utf8")
        metadata["digest"] = f"proto:{hashlib.sha256(encoded).digest().hex()}"

        final_manifest: Dict[str, Any] = copy.deepcopy(manifest)
        final_manifest["metadata"] = metadata

        return final_manifest

    def verify(self) -> bool:
        """
        Check if the protocol implements all interactions of its specification.

        Returns:
            bool: True if the protocol implements the role, False otherwise.
        """
        if self._interactions is None:
            # No specification to verify against
            return True

        message_handlers = (
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
    def compute_digest(manifest: Dict[str, Any]) -> str:
        """
        Compute the digest of a given manifest.

        Args:
            manifest (Dict[str, Any]): The manifest to compute the digest for.

        Returns:
            str: The computed digest.
        """
        cleaned_manifest = copy.deepcopy(manifest)
        if "metadata" in cleaned_manifest:
            del cleaned_manifest["metadata"]
        cleaned_manifest["metadata"] = {}

        encoded = json.dumps(cleaned_manifest, indent=None, sort_keys=True).encode(
            "utf8"
        )
        return f"proto:{hashlib.sha256(encoded).digest().hex()}"
