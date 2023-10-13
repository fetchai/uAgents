"""Dialogue class aka. blueprint for protocols"""
import functools
import graphlib
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional, Set, Type, Union
from uuid import UUID

from uagents import Context, Model, Protocol
from uagents.storage import KeyValueStore

DEFAULT_SESSION_TIMEOUT = 10

JsonStr = str

MessageCallback = Callable[["Context", str, Any], Awaitable[None]]


class Node:
    """
    A node represents a state in the dialogue.
    """

    def __init__(
        self,
        name: str,
        description: str,
    ) -> None:
        self.name = name
        self.description = description


class Edge:
    """
    An edge represents a transition between two states in the dialogue.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parent: Node,  # tail
        child: Node,  # head
        model: Type[Model] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.parent = parent
        self.child = child
        self._model = model

    @property
    def model(self) -> Type[Model]:
        """The message model type that is associated with the edge."""
        return self._model

    @model.setter
    def model(self, model: Type[Model]) -> None:
        self._model = model


class Dialogue(Protocol):
    """
    A Dialogue is the local representation of the dialogue.

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
        nodes: list[Node] | None = None,
        edges: list[Edge] | None = None,
        rules: dict[
            Type[Model], set[Type[Model]]
        ] = None,  # replace with nodes and edges
        agent_address: Optional[str] = "",  # TODO: discuss storage naming
        timeout: int = DEFAULT_SESSION_TIMEOUT,
        max_nr_of_messages: int = 100,  # TODO: enforce limit
    ) -> None:
        self._name = name

        self._nodes = nodes or []
        self._edges = edges or []

        # TODO: <graph checks happen here>

        self._rules = self._build_rules(
            rules
        )  # graph of dialogue represented by message digests
        self._cyclic = False
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
        self.max_nr_of_messages = max_nr_of_messages  # TODO: implement feature
        super().__init__(name=self._name, version=version)

        # for edge in self._edges:
        #     pass

        @self.on_interval(1)
        async def cleanup_dialogue(_ctx: Context):
            """
            Cleanup the dialogue.

            Deletes sessions that have not been used for a certain amount of time.
            The task runs every second so the configured timeout is currently
            measured in seconds as well (interval time * timeout parameter).
            Sessions with 0 as timeout will never be deleted.
            """
            mark_for_deletion = []
            for session_id, session in self._sessions.items():
                timeout = session[-1]["timeout"]
                if (
                    timeout > 0
                    and datetime.fromtimestamp(session[-1]["timestamp"])
                    + timedelta(seconds=timeout)
                    < datetime.now()
                ):
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

    @property
    def is_cyclic(self) -> bool:
        """
        Property to determine whether the dialogue has cycles.

        Returns:
            bool: True if the dialogue is cyclic, False otherwise.
        """
        return self._cyclic

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

    def _auto_add_message_handler(self) -> None:
        # iterate over all edges and add respective message handlers
        return

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
        if graph._find_cycle():  # pylint: disable=protected-access
            self._cyclic = True
            return list(self._rules.keys())[0]
        return list(graph.static_order())[-1]

        # programmatic way of finding the starter node
        # handled_models = set()
        # for model, replies in RULESET.items():
        #     for reply in RULESET[model]:
        #         handled_models.add(reply)
        #         assert reply in RULESET, f"Reply {reply} not in ruleset!"
        # # assert len(handled_models) == len(RULESET), "Not all models are handled!"
        # nodes_without_entry = set(RULESET.keys()).difference(handled_models)

        # print(nodes_without_entry)  # must be entry node, may be multiple (?)

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
        message_type: str,
        sender: str,
        receiver: str,
        content: JsonStr,
        **kwargs,
    ) -> None:
        """Add a message to a session within the dialogue instance."""
        if session_id is None:
            raise ValueError("Session ID must not be None!")
        if session_id not in self._sessions:
            self._add_session(session_id)
        self._sessions[session_id].append(
            {
                "message_type": message_type,
                "sender": sender,
                "receiver": receiver,
                "message_content": content,
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

    def _update_transition_model(self, edge: Edge, model: Type[Model]) -> None:
        self._edges[self._edges.index(edge)].model = model

    def on_state_transition(self, edge: Edge, model: Type[Model]):
        """
        Main decorator to register a message handler for the dialogue.
        The Model in this case is the message model type but it refers to the
        Edge which is the transition between two states.

        Args:
            edge (Edge): Edge object that represents the transition.
            model (Type[Model]): Message model type.
        """

        def decorator_on_state_transition(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            # TODO: find edge first
            self._update_transition_model(edge, model)
            return handler

        # TODO: recalculate manifest after each update and re-register the protocol
        return decorator_on_state_transition
