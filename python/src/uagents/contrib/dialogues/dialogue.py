"""Dialogue class aka. blueprint for protocols"""
from enum import Enum
from typing import Optional, Type
from uuid import UUID, uuid4

from pydantic import Field
from src.uagents import Model, Protocol

JsonStr = str
SenderStr = str

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
        name: Optional[str] = None,
        version: Optional[str] = None,
        rules: dict[Type[Model], list[Type[Model]]] = None,
        dialogue_id: Optional[UUID] = None,
        starter: Optional[Type[Model]] = None,
        ender: Optional[type[Model] | set[type[Model]]] = None,
    ) -> None:
        self._id = dialogue_id or uuid4()  # id of the dialogue
        self._rules = self._build_rules(rules)  # which messages are allowed
        self._starter = Model.build_schema_digest(
            starter
        )  # first message of the dialogue
        self._ender = set(
            Model.build_schema_digest(e) for e in ender
        )  # last message of the dialogue
        self._current_state: str = None  # current state of the dialogue (as digest)
        self._sessions: dict[
            DialogueLabel, list[(SenderStr, JsonStr)]
        ] = {}  # session + message storage
        self._lifetime = 0
        super().__init__(name=name, version=version)
        self._is_dialogue = True

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

    @property
    def is_dialogue(self) -> bool:
        """
        Property to access the is_dialogue flag of the dialogue.

        Returns:
            bool: True if the protocol is a dialogue, False otherwise.
        """
        return self._is_dialogue

    def is_starter(self, digest: str) -> bool:
        return self._starter == digest

    def is_ender(self, digest: str) -> bool:
        return digest in self._ender

    def _build_rules(self, rules: dict[Model, list[Model]]) -> dict[str, list[str]]:
        """
        Build the rules for the dialogue.

        Args:
            rules (dict[Model, list[Model]]): Rules for the dialogue.

        Returns:
            dict[str, list[str]]: Rules for the dialogue.
        """
        return [
            {
                Model.build_schema_digest(key): [
                    Model.build_schema_digest(v) for v in values
                ]
            }
            for key, values in rules.items()
        ]

    def update_state(self, digest: str) -> None:
        self._current_state = digest

    def add_session(self, session_id, sender, receiver, message) -> None:
        self._sessions[session_id] = []
        self._sessions[session_id].append((sender, receiver, message))

    def cleanup_session(self, session_id) -> None:
        self._sessions.pop(session_id)

    def add_message(self, session_id, sender, receiver, message) -> None:
        return
        session = self._sessions.get(session_id)

    def _get_messages_by_session(self, session_id: UUID):
        return [msg for msg in self._messages if msg[0] == session_id]

    def _is_valid_message(self, session_id: UUID, msg: type[Model]) -> bool:
        # get last message from session stack
        messages = self._get_messages_by_session(session_id)
        if not messages:
            return False
        last_msg = messages[-1][1]
        allowed_msgs = self._rules.get(Model.build_schema_digest(last_msg), [])
        # check if message is allowed
        if msg not in allowed_msgs:
            return False
        return True
