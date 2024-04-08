"""Dialogue class aka. blueprint for protocols."""

import functools
import graphlib
import warnings
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type
from uuid import UUID

from uagents import Context, Model, Protocol
from uagents.storage import KeyValueStore

DEFAULT_SESSION_TIMEOUT_IN_SECONDS = 100
TARGET_UUID_VERSION = 4

JsonStr = str

MessageCallback = Callable[["Context", str, Any], Awaitable[None]]


class Node:
    """A node represents a state in the dialogue."""

    def __init__(
        self,
        name: str,
        description: str,
        initial: bool = False,
    ) -> None:
        self.name = name
        self.description = description
        self.initial = initial
        self.final = False


class Edge:
    """An edge represents a transition between two states in the dialogue."""

    def __init__(
        self,
        name: str,
        description: str,
        parent: Optional[Node],  # tail
        child: Node,  # head
    ) -> None:
        self.name = name
        self.description = description
        self.parent = parent
        self.child = child
        self._model = None
        self._func = None

    @property
    def model(self) -> Optional[Type[Model]]:
        """The message model type that is associated with the edge."""
        return self._model

    @model.setter
    def model(self, model: Type[Model]) -> None:
        """Set the message model type for the edge."""
        self._model = model

    @property
    def func(self) -> MessageCallback:
        """The message handler that is associated with the edge."""
        return self._func

    def set_default_behaviour(self, model: Type[Model], func: MessageCallback):
        """Set the default behaviour for the edge."""
        self._model = model
        self._func = func


class Dialogue(Protocol):
    """
    A dialogue is a protocol with added functionality to handle the enforcement
    of a sequence of messages.
    The instance of this class is the local representation of the dialogue,
    i.e. the definition of a pattern of messages that are exchanged between
    two participants.

    When defining a pattern of Nodes and Edges, the dialogue will automatically
    be validated for cycles and the rules will be derived from the graph.

    The only thing left to do is to add message handlers for the edges in a
    known fashion, i.e. the message handler for an edge must be decorated with
    the edge name and the message model type.
    The message handler will be registered automatically and the message model
    will be used to validate the message content.

    Ex.:
        @dialogue._on_state_transition("edge_name", MessageModel)
        async def handler(ctx: Context, sender: str, message: MessageModel):
            pass

    A common practice is to add additional decorators to the pattern definition
    to simplify the usage of the dialogue class. This can be done by creating
    creating additional decorators that call the _on_state_transition method.
    Ex.:
        def on_init(model: Type[Model]):
            return super()._on_state_transition("edge_name", model)

    and then use it like this:
        @pattern.on_init(MessageModel)
        async def handler(ctx: Context, sender: str, message: MessageModel):
            pass

    The current features include:
    - A graph representation of the dialogue, which is used to validate the
        sequence of messages.
    - Session handling which includes a session storage that contains all the
        messages that were exchanged between two participants.
    - Sessions will automatically be deleted after a certain amount of time.
    - Access to the dialogue history through ctx.dialogue (see Context class).
    """

    def __init__(
        self,
        name: str,
        agent_address: str,  # tbd: storage naming and handling
        version: Optional[str] = None,
        nodes: List[Node] | None = None,
        edges: List[Edge] | None = None,
        timeout: int = DEFAULT_SESSION_TIMEOUT_IN_SECONDS,
    ) -> None:
        self._name = name

        self._nodes = nodes or []
        self._edges = edges or []
        self._graph: Dict[str, List[str]] = self._build_graph()  # by nodes
        self._rules: Dict[str, List[str]] = self._build_rules()  # by edges
        self._digest_by_edge: Dict[str, str] = {
            edge.name: Model.build_schema_digest(edge.model) if edge.model else ""
            for edge in self._edges
        }  # store the message models that are associated with an edge

        self._cyclic = False
        self._starter = self._build_starter()  # first message of the dialogue
        self._ender = self._build_ender()  # last message(s) of the dialogue

        self._timeout = timeout
        self._storage = KeyValueStore(
            f"{agent_address[0:16]}_dialogues"
        )  # persistent session + message storage
        self._sessions: Dict[UUID, List[Any]] = (
            self._load_storage()
        )  # volatile session + message storage
        self._states: Dict[
            UUID, str
        ] = {}  # current state of the dialogue (as edge digest) per session
        self._custom_session: UUID | None = None

        super().__init__(name=self._name, version=version)

        # if a model exists for an edge, register the handler automatically
        self._auto_add_message_handler()

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
                    self.cleanup_conversation(session_id)

        # radical but effective
        self.on_message = None
        self.on_query = None

    @property
    def rules(self) -> Dict[str, List[str]]:
        """
        Property to access the rules of the dialogue.

        Returns:
            Dict[str, List[str]]: Dictionary of rules represented by edges.
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

    @property
    def nodes(self) -> List[Node]:
        return self._nodes

    @property
    def edges(self) -> List[Edge]:
        return self._edges

    def get_overview(self) -> Dict:
        """
        Get an overview of the dialogue structure.

        Returns:
            Dict: Manifest like representation of the dialogue structure.
        """
        return (
            {
                "nodes": [node.__dict__ for node in self._nodes],
                "edges": [
                    {
                        "name": edge.name,
                        "description": edge.description,
                        "parent": edge.parent.name if edge.parent else None,
                        "child": edge.child.name,
                        "model": edge.model.__name__ if edge.model else None,
                        "starter": edge.starter,
                        "ender": edge.ender,
                    }
                    for edge in self._edges
                ],
            }
            if self._nodes
            else {}
        )

    def _build_graph(self) -> Dict[str, List[str]]:
        """
        Build the graph of the dialogue while showing the state relations.

        Returns:
            Dict[str, List[str]]: List of states and their relations.
        """
        graph = {}
        for node in self._nodes:
            graph.setdefault(node.name, [])
        for edge in self._edges:
            if edge.parent:
                graph.setdefault(edge.parent.name, []).append(edge.child.name)
        return graph

    def _build_rules(self) -> Dict[str, List[str]]:
        """
        Build the rules for the dialogue.
        Which replies are allowed after a certain message.

        Returns:
            Dict[str, List[str]]: Rules for the dialogue.
        """
        out = {edge.name: [] for edge in self._edges}
        for edge in self._edges:
            for inner_edge in self._edges:
                if inner_edge.parent and inner_edge.parent.name == edge.child.name:
                    out[edge.name].append(inner_edge.name)

        graph = graphlib.TopologicalSorter(out)
        if graph._find_cycle():  # pylint: disable=protected-access
            self._cyclic = True
        return out

    def _build_starter(self) -> str:
        """Build the starting message of the dialogue."""
        starter_nodes = list(filter(lambda n: n.initial, self._nodes))
        # check if starter property has been set and if there is only one
        if len(starter_nodes) > 1:
            raise ValueError("Dialogue has more than one entry point!")

        edges_without_entry = list(filter(lambda e: e.parent is None, self._edges))
        if not edges_without_entry and starter_nodes:
            # if there is a starter node and no edge without parent we need to
            # validate if the graph is correct
            starters = list(filter(lambda e: e.parent is starter_nodes[0], self._edges))
            if starters:
                self._edges[self._edges.index(starters[0])].starter = True
                return starters[0].name
        if starter_nodes and edges_without_entry:
            warnings.warn(
                "There is a starter node and an edge without parent present. "
                "The edge without a parent takes precedence!",
                SyntaxWarning,
                stacklevel=2,
            )
        if len(edges_without_entry) > 1:
            raise ValueError("Dialogue has more than one entry point!")
        if edges_without_entry:
            self._edges[self._edges.index(edges_without_entry[0])].starter = True
            return edges_without_entry[0].name
        raise ValueError("Dialogue has no entry point!")

    def _build_ender(self) -> set[str]:
        """Build the last message(s) of the dialogue and set final state."""
        for node, edges in self._graph.items():
            if not edges:
                self._nodes[
                    self._nodes.index(next(n for n in self._nodes if n.name == node))
                ].final = True
        enders = set()
        for edge in self._edges:
            if edge.child.final:
                enders.add(edge.name)
                edge.ender = True
        return enders

    def is_starter(self, digest: str) -> bool:
        """
        Return True if the digest is the starting message of the dialogue.
        False otherwise.
        """
        return self._digest_by_edge[self._starter] == digest

    def is_ender(self, digest: str) -> bool:
        """
        Return True if the digest is the last message of the dialogue.
        False otherwise.
        """
        return digest in [self._digest_by_edge[edge] for edge in self._ender]

    def get_current_state(self, session_id: UUID) -> str:
        """Get the current state of the dialogue for a given session."""
        return self._states.get(session_id, "")

    def is_finished(self, session_id: UUID) -> bool:
        """
        Return True if the current state is (one of) the ending state(s).
        False otherwise.
        """
        return self.is_ender(self.get_current_state(session_id))

    def _auto_add_message_handler(self) -> None:
        """Automatically add message handlers for edges with models."""
        for edge in self._edges:
            if edge.model and edge.func:
                self._add_message_handler(edge.model, edge.func, None, False)

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

    def cleanup_conversation(self, session_id: UUID) -> None:
        """Removes all messages related with the given session from the dialogue instance."""
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
        """Add a message to the conversation of the given session within the dialogue instance."""
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
                "timeout": self._timeout,
                **kwargs,
            }
        )
        self._update_session_in_storage(session_id)

    def get_conversation(self, session_id) -> List[Any]:
        """
        Return the conversation of the given session from the dialogue instance.

        This includes all messages that were sent and received for the session.
        """
        return self._sessions.get(session_id)

    def get_edge(self, edge_name: str) -> Edge:
        """Return an edge from the dialogue instance."""
        return next(edge for edge in self._edges if edge.name == edge_name)

    def _resolve_mapping(self, msg_digest: str) -> str:
        """Resolve the mapping of a message digest to a message model."""
        return next(k for k, v in self._digest_by_edge.items() if v == msg_digest)

    def is_valid_message(self, session_id: UUID, msg_digest: str) -> bool:
        """
        Check if a message is valid for a given session.

        Args:
            session_id (UUID): The ID of the session to check the message for.
            msg_digest (str): The digest of the message to check.

        Returns:
            bool: True if the message is valid, False otherwise.
        """
        if session_id not in self._sessions or len(self._sessions[session_id]) == 0:
            return self.is_starter(msg_digest)

        transition = self._resolve_mapping(msg_digest)
        current_state = self.get_current_state(session_id)
        current_state_mapped = self._resolve_mapping(current_state)
        allowed_msgs = self._rules.get(current_state_mapped, [])
        return transition in allowed_msgs

    def is_valid_reply(self, in_msg: str, out_msg: str) -> bool:
        """
        Check if a reply is valid for a given message.

        Args:
            in_msg (str): The digest of the message to check the reply for.
            out_msg (str): The digest of the reply to check.

        Returns:
            bool: True if the reply is valid, False otherwise.
        """
        return self._resolve_mapping(out_msg) in self._rules.get(
            self._resolve_mapping(in_msg), []
        )

    def is_included(self, msg_digest: str) -> bool:
        """
        Check if a message is included in the dialogue.

        Args:
            msg_digest (str): The digest of the message to check.

        Returns:
            bool: True if the message is included, False otherwise.
        """
        return msg_digest in self._digest_by_edge.values()

    def _load_storage(self) -> Dict[UUID, List[Any]]:
        """Load the sessions from the storage."""
        cache: Optional[Dict] = self._storage.get(self.name)
        return (
            {UUID(session_id): session for session_id, session in cache.items()}
            if cache
            else {}
        )

    def _update_session_in_storage(self, session_id: UUID) -> None:
        """Update a session in the storage."""
        cache: Dict = self._storage.get(self.name) or {}
        cache[str(session_id)] = self._sessions[session_id]
        self._storage.set(self.name, cache)

    def _remove_session_from_storage(self, session_id: UUID) -> None:
        """Remove a session from the storage."""
        cache: Dict = self._storage.get(self.name) or {}
        session = str(session_id)
        if session in cache:
            cache.pop(session)
        self._storage.set(self.name, cache)

    def _update_transition_model(self, edge: Edge, model: Type[Model]) -> None:
        """Update the message model for a transition."""
        self._digest_by_edge[edge.name] = Model.build_schema_digest(model)
        self._edges[self._edges.index(edge)].model = model

    def _on_state_transition(self, edge_name: str, model: Type[Model]):
        """
        Main decorator to register a message handler for the dialogue.
        The Model in this case is the message model type but it refers to the
        Edge which is the transition between two states.

        Replies will not be validated based on the decorator parameters but
        on the graph and its rules instead.

        Args:
            edge (Edge): Edge object that represents the transition.
            model (Type[Model]): Message model type.
        """
        if edge_name not in self._digest_by_edge:
            raise ValueError("Edge does not exist in the dialogue!")

        def decorator_on_state_transition(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            edge = self.get_edge(edge_name)
            self._update_transition_model(edge, model)
            self._add_message_handler(model, func, None, False)
            return handler

        # NOTE: recalculate manifest after each update and re-register /w agent
        return decorator_on_state_transition

    @property
    def custom_session(self) -> UUID | None:
        """Return the custom session ID."""
        return self._custom_session

    def set_custom_session_id(self, uuid: UUID) -> None:
        """
        Start a new session with the given ID.

        This method will create a session with the given UUID and uses that
        ID the next time that a starter message is sent.
        """
        if uuid.version != TARGET_UUID_VERSION:
            raise ValueError("Session ID must be of type UUID v4!")
        if uuid in self._sessions:
            raise ValueError("Session ID already exists!")
        if self._custom_session:
            raise ValueError("Custom session ID already set!")
        self._custom_session = uuid

    def reset_custom_session_id(self) -> None:
        """Reset the custom session ID."""
        self._custom_session = None

    def manifest(self) -> Dict[str, Any]:
        """
        This method will add the dialogue structure to the original manifest
        and recalculate the digest.
        """

        updated_manifest = super().manifest() | {
            "nodes": [node.__dict__ for node in self._nodes],
            "edges": [
                {
                    "name": edge.name,
                    "description": edge.description,
                    "parent": edge.parent.name if edge.parent else None,
                    "child": edge.child.name,
                    "model": edge.model.__name__ if edge.model else None,
                    "starter": edge.starter,
                    "ender": edge.ender,
                }
                for edge in self._edges
            ],
        }
        new_digest = Protocol.compute_digest(updated_manifest)
        updated_manifest["metadata"]["digest"] = new_digest
        return updated_manifest
