"""Dialogue class aka. blueprint for protocols"""
from enum import Enum
from typing import Optional, Type
from uuid import UUID, uuid4

from pydantic import Field
from uagents import Model, Protocol
from uagents.storage import KeyValueStore

JsonStr = str
SenderStr = str
ReceiverStr = str

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
        rules: dict[Type[Model], list[Type[Model]]] = None,
        dialogue_id: Optional[UUID] = None,
        starter: Optional[Type[Model]] = None,
        ender: Optional[type[Model] | set[type[Model]]] = None,
        agent_address: Optional[str] = "",
    ) -> None:
        self._id = dialogue_id or uuid4()  # id of the dialogue
        self._rules = self._build_rules(
            rules
        )  # DAG of dialogue represented by message digests
        self._starter = Model.build_schema_digest(
            starter
        )  # first message of the dialogue
        self._ender = set(
            Model.build_schema_digest(e) for e in ender
        )  # last message of the dialogue
        self._states: dict[
            UUID, str
        ] = {}  # current state of the dialogue (as digest) per session
        self._sessions: dict[
            UUID, list[(SenderStr, ReceiverStr, JsonStr)]
        ] = {}  # session + message storage
        self._lifetime = 0
        self._storage = KeyValueStore(f"{agent_address[0:16]}_dialogues")
        super().__init__(name=name, version=version)

        self._storage.clear()  # TODO: remove after testing

    @property
    def id(self) -> UUID:
        """
        Property to access the id of the dialogue.

        :return: UUID: id of the dialogue
        """
        return self._id

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
            self.add_session(session_id)

    def add_session(self, session_id: UUID) -> None:
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
    ) -> None:
        """Add a message to a session within the dialogue instance."""
        if session_id not in self._sessions:
            self.add_session(session_id)
        self._sessions[session_id].append(
            {
                "message": message,
                "sender": sender,
                "receiver": receiver,
                "content": content,
            }
        )
        self._update_session_in_storage(session_id)

    def get_session(self, session_id) -> list[(SenderStr, ReceiverStr, JsonStr)]:
        """
        Return a session from the dialogue instance.

        This includes all messages that were sent and received for the session.
        TODO: currently only received messages
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
