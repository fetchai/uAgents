"""Dialogue class aka. blueprint for protocols"""
import functools
from enum import Enum
from typing import Optional, Set, Type, Union
from uuid import UUID, uuid4

from pydantic import Field
from src.uagents import Model
from src.uagents.context import MessageCallback

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
    dialogue_reference: UUID = Field(description="Id of the dialogue")
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


class Dialogue:
    """
    - This should be the local representation of the dialogue.
    - Each participant will have its own instance of this class per dialogue.
    - A storage will contain all the dialogues that took place, which may be
      automatically deleted after a certain amount of time.
    - is meant to simplify the handling of individual messages
    """

    def __init__(
        self,
        rules: dict[Type[Model], list[Type[Model]]],
        dialogue_id: Optional[UUID] = None,
    ) -> None:
        self._id = dialogue_id or uuid4()  # id of the dialogue
        self._rules = self._build_rules(rules)  # which messages are allowed
        self._states: dict[str, Type[Model]] = {}  # list of states
        self._models: dict[str, Type[Model]] = {}
        self._signed_message_handlers: dict[str, MessageCallback] = {}
        self._unsigned_message_handlers: dict[str, MessageCallback] = {}
        self._replies: dict[str, dict[str, Type[Model]]] = {}
        self._sessions: dict[DialogueLabel, list[UUID]] = {}  # session storage
        self._messages: list[(str, DialogueMessage)] = []  # message storage
        self._lifetime = 0

    @property
    def id(self) -> UUID:
        """
        Property to access the id of the dialogue.

        :return: UUID: id of the dialogue
        """
        return self._id

    @property
    def rules(self) -> dict[Model, list[Model]]:
        return self._rules

    @property
    def models(self) -> dict[str, Type[Model]]:
        """
        Property to access the registered models.

        Returns:
            Dict[str, Type[Model]]: Dictionary of registered models with schema digests as keys.
        """
        return self._models

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

    def _get_messages_by_session(self, session_id: UUID):
        return [msg for msg in self._messages if msg[0] == session_id]

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

    def _is_valid_message(self, session_id: UUID, msg: DialogueMessage) -> bool:
        # get last message from session stack
        messages = self._get_messages_by_session(session_id)
        if not messages:
            return False
        last_msg = messages[-1][1]
        # check if message is allowed
        return True  # TODO

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
    ):
        # model_digest = Model.build_schema_digest(model)
        # assert model_digest in self._models, f"Model {model} not found"

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


NOTES2 = """
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


# message needed to synchronize the dialogue partners
# class DialogueStatus(Model):
#     status: str


# agent = Agent()
# agent.on_message(DialogueStatus, DialogueStatus)


# x = Protocol(name="dialogue", version="0.1")
# x.on_message(DialogueStatus, DialogueStatus)


# @dialogue_protocol.on_message(DialogueStatus, DialogueStatus, "INIT")
# async def bla1(ctx: Context, sender: str, msg: DialogueStatus) -> None:
#     pass


# @dialogue_protocol.on_message(DialogueStatus, DialogueStatus, "MESSAGE")
# async def bla2(ctx: Context, sender: str, msg: DialogueStatus) -> None:
#     pass


# @dialogue_protocol.on_message(DialogueStatus, DialogueStatus, "ACCEPT")
# async def bla3(ctx: Context, sender: str, msg: DialogueStatus) -> None:
#     pass


# @dialogue_protocol.on_message(DialogueStatus, DialogueStatus, "FINISH")
# async def bla4(ctx: Context, sender: str, msg: DialogueStatus) -> None:
#     pass
