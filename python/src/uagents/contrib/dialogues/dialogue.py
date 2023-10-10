"""Dialogue class aka. blueprint for protocols"""
import graphlib
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Type, Callable, Awaitable, Union, Set
from uuid import UUID

import functools
from pydantic import Field
from uagents import Context, Model, Protocol
from uagents.storage import KeyValueStore



JsonStr = str
SenderStr = str
ReceiverStr = str


MessageCallback = Callable[["Context", str, Any], Awaitable[None]]

NOTES = """
- A dialogue is a sequence of messages
- Each dialogue has a unique identifier
- A dialogue is identified by a DialogueLabel
- A dialogue will have a list of messages
- A dialogue will have a lifetime
- A dialogue will always have 1 "init" state in the beginning and a "finish"
  state in the end

Q: where to store the messages? Separate from ctx.storage?
Q: how to handle the lifetime of the dialogues? Block or time based?

- msg has a session id
- we can use this session id to identify the dialogue
- one dialogue id can have multiple messages and ids

- less interest in generic solution
- we focus on set of structures -> to come up with client abstractions
- time log confirmation dialogue
- see dialogue as a blueprint for protocols

- dialogue stores only the rules
- you would still need to define the states and message handlers

- try to simplify the handling of individual messages
- single model for state (across whole flow or dialogue)
- dialogue would be a layer on top of  protocols and messages

- dialogue object has custom set of decorators (to build on the learnings)

start with:
- simple dialogue with simple rules
- query -> response -> accept/decline -> finish
- success, failure, timeout, retry
"""


class Performative(str, Enum):
    INIT = "init"
    ACCEPT = "accept"
    DECLINE = "decline"
    MESSAGE = "message"
    FINISH = "finish"


class DialogueMessage(Model):
    performative: Performative = Field(
        description=("Description of what is being done (may be defined by a protocol)")
    )
    contents: dict = Field(
        description=(
            "Content of the message. " "This will vary based on the Performative."
        )
    )
    is_incoming: bool = Field(
        description=("True if the message is incoming, False if outgoing"),
        default=False,
    )
    target: str = Field(
        description=("Address of the agent that is the target of the message")
    )
    sender: str = Field(
        description=("Address of the agent that is the sender of the message")
    )


# To give the dialogue a context and to enable dialogue comparison
class DialogueLabel(Model):
    session_id: UUID = Field(description="Id of the dialogue")
    dialogue_starter: str = Field(
        description="Address of the agent that started the dialogue"
    )
    dialogue_receiver: str = Field(
        description="Address of the agent that is the receiver of the dialogue"
    )


# The actual message that will be sent to the other agent
# May need some more fields
class DialogueWrapper(Model):
    dialogue_label: DialogueLabel
    dialogue_message: DialogueMessage


class Dialogue(Protocol):
    """
    - This should be the local representation of the dialogue.
    - Each participant will have its own instance of this class per dialogue.
    - A storage will contain all the dialogues that took place, which may be
      automatically deleted after a certain amount of time.
    - is meant to simplify the handling of individual messages
    """

    def __init__(
        self,
        name: str,  # mandatory, due to storage naming
        version: Optional[str] = None,
        rules: dict[Type[Model], set[Type[Model]]] = None,
        agent_address: Optional[str] = "",  # TODO: discuss storage naming
        timeout: int = 10,  # should be constant
    ) -> None:
        self._name = name
        self._rules = self._build_rules(
            rules
        )  # DAG of dialogue represented by message digests
        self._starter = self._build_starter()  # first message of the dialogue
        self._ender = self._build_ender()  # last message(s) of the dialogue
        self._states: dict[
            UUID, str
        ] = {}  # current state of the dialogue (as digest) per session
        self._lifetime = timeout
        self._storage = KeyValueStore(
            f"{agent_address[0:16]}_dialogues"
        )  # persistent session + message storage
        self._sessions: dict[
            UUID, list[Any]
        ] = self._load_storage()  # volatile session + message storage
        super().__init__(name=self._name, version=version)

        @self.on_interval(1)
        async def cleanup_dialogue(_ctx: Context):
            """
            Cleanup the dialogue.

            Deletes sessions that have not been used for a certain amount of time.
            Sessions with 0 as timeout will never be deleted.
            """
            mark_for_deletion = []
            for session_id, session in self._sessions.items():
                timeout = session[-1]["timeout"]
                if timeout > 0 and session[-1][
                    "timestamp"
                ] + timeout < datetime.timestamp(datetime.now()):
                    mark_for_deletion.append(session_id)
            if mark_for_deletion:
                for session_id in mark_for_deletion:
                    self.cleanup_session(session_id)

    @property
    def rules(self) -> dict[str, list[str]]:
        """
        Property to access the rules of the dialogue.

        Returns:
            dict[str, list[str]]: Dictionary of rules with schema digests as keys.
        """
        return self._rules

    def get_current_state(self, session_id: UUID) -> str:
        """Get the current state of the dialogue for a given session."""
        return self._states[session_id] if session_id in self._states else ""

    def is_starter(self, digest: str) -> bool:
        """
        Return True if the digest is the starting message of the dialogue.
        False otherwise.
        """
        return self._starter == digest

    def is_ender(self, digest: str) -> bool:
        """
        Return True if the digest is the last message of the dialogue.
        False otherwise.
        """
        return digest in self._ender

    def _build_rules(self, rules: dict[Model, list[Model]]) -> dict[str, list[str]]:
        """
        Build the rules for the dialogue.

        Args:
            rules (dict[Model, list[Model]]): Rules for the dialogue.

        Returns:
            dict[str, list[str]]: Rules for the dialogue.
        """
        return {
            Model.build_schema_digest(key): [
                Model.build_schema_digest(v) for v in values
            ]
            for key, values in rules.items()
        }

    def _build_starter(self) -> str:
        """Build the starting message of the dialogue."""
        graph = graphlib.TopologicalSorter(self._rules)
        return list(graph.static_order())[-1]

    def _build_ender(self) -> set[str]:
        """Build the last message(s) of the dialogue."""
        return set(model for model in self._rules if not self._rules[model])

    def update_state(self, digest: str, session_id: UUID) -> None:
        """
        Update the state of a dialogue session and create a new session
        if it does not exist.

        Args:
            digest (str): The digest of the message to update the state with.
            session_id (UUID): The ID of the session to update the state for.
        """
        self._states[session_id] = digest
        if session_id not in self._sessions:
            self._add_session(session_id)

    def _add_session(self, session_id: UUID) -> None:
        """Create a new session in the dialogue instance."""
        self._sessions[session_id] = []

    def cleanup_session(self, session_id: UUID) -> None:
        """Remove a session from the dialogue instance."""
        self._sessions.pop(session_id)
        self._remove_session_from_storage(session_id)

    def add_message(
        self,
        session_id: UUID,
        message: str,
        sender: SenderStr,
        receiver: ReceiverStr,
        content: JsonStr,
        **kwargs,
    ) -> None:
        """Add a message to a session within the dialogue instance."""
        if session_id not in self._sessions:
            self._add_session(session_id)
        self._sessions[session_id].append(
            {
                "message": message,
                "sender": sender,
                "receiver": receiver,
                "content": content,
                "timestamp": datetime.timestamp(datetime.now()),
                "timeout": self._lifetime,
                **kwargs,
            }
        )
        self._update_session_in_storage(session_id)

    def get_session(self, session_id) -> list[Any]:
        """
        Return a session from the dialogue instance.

        This includes all messages that were sent and received for the session.
        """
        return self._sessions.get(session_id)

    def is_valid_message(self, session_id: UUID, msg_digest: str) -> bool:
        """
        Check if a message is valid for a given session.

        Args:
            session_id (UUID): The ID of the session to check the message for.
            msg_digest (str): The digest of the message to check.

        Returns:
            bool: True if the message is valid, False otherwise.
        """
        if session_id not in self._sessions:
            return self.is_starter(msg_digest)
        allowed_msgs = self._rules.get(self.get_current_state(session_id), [])
        return msg_digest in allowed_msgs

    def is_included(self, msg_digest: str) -> bool:
        """
        Check if a message is included in the dialogue.

        Args:
            msg_digest (str): The digest of the message to check.

        Returns:
            bool: True if the message is included, False otherwise.
        """
        return msg_digest in self._rules

    def _load_storage(self) -> dict[UUID, list[Any]]:
        """Load the sessions from the storage."""
        cache: dict = self._storage.get(self.name)
        return (
            {UUID(session_id): session for session_id, session in cache.items()}
            if cache
            else {}
        )

    def _update_session_in_storage(self, session_id: UUID) -> None:
        """Update a session in the storage."""
        cache: dict = self._storage.get(self.name) or {}
        cache[str(session_id)] = self._sessions[session_id]
        self._storage.set(self.name, cache)

    def _remove_session_from_storage(self, session_id: UUID) -> None:
        """Remove a session from the storage."""
        cache: dict = self._storage.get(self.name)
        cache.pop(str(session_id))
        self._storage.set(self.name, cache)

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
    ):
        """
        Decorator to register a message handler for the protocol.
        Compared to the basic decorator defined in the Protocol module, this descorator
        additionally verifies if the given interaction is allowed in the rules set
        of this Dialogue.

        Args:
            model (Type[Model]): The message model type.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]], optional): The associated
            reply types. Defaults to None.
            allow_unverified (Optional[bool], optional): Whether to allow unverified messages.
            Defaults to False.

        Returns:
            Callable: The decorator to register the message handler.
        """

        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            if replies is not None:
                repliez = set()
                if isinstance(replies, set):
                    repliez = replies
                if isinstance(replies, type) and issubclass(replies, Model):
                    repliez = {replies}
                for rep in repliez:
                    if not Model.build_schema_digest(rep) in self._rules.get(
                        Model.build_schema_digest(model), []
                    ):
                        raise ValueError(
                            "Interaction not allowed! Please check the rules defined for the used dialogue."
                        )
                self._add_message_handler(model, func, replies, allow_unverified)

            return handler

        return decorator_on_message
