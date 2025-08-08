"""Dialogue class aka. blueprint for protocols."""

import functools
import warnings
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from uagents_core.models import ErrorMessage
from uagents_core.types import DeliveryStatus, JsonStr, MsgStatus

from uagents import Context, Model, Protocol
from uagents.storage import KeyValueStore, StorageAPI

DEFAULT_SESSION_TIMEOUT_IN_SECONDS = 60
TARGET_UUID_VERSION = 4

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
        parent: Node | None,  # tail
        child: Node,  # head
    ) -> None:
        self.name = name
        self.description = description
        self.parent = parent
        self.child = child
        self.starter: bool = False
        self.ender: bool = False
        self._model: type[Model] | None = None
        self._func: MessageCallback | None = None
        self._efunc: MessageCallback | None = None

    @property
    def model(self) -> type[Model] | None:
        """The message model type that is associated with the edge."""
        return self._model

    @model.setter
    def model(self, model: type[Model]) -> None:
        """Set the message model type for the edge."""
        self._model = model

    @property
    def func(self) -> MessageCallback | None:
        """The message handler that is associated with the edge."""
        return self._func

    @func.setter
    def func(self, func: MessageCallback) -> None:
        """Set the message handler that will be called when a message is received."""
        self._func = func

    @property
    def efunc(self) -> MessageCallback | None:
        """The edge handler that is associated with the edge."""
        return self._efunc

    def set_edge_handler(self, model: type[Model], func: MessageCallback) -> None:
        """
        Set the edge handler that will be called when a message is received
        This handler can not be overwritten by a decorator.
        """
        if self._model and self._model is not model:
            raise ValueError("Functionality already set with a different model!")
        self._model = model
        self._efunc = func

    def set_message_handler(self, model: type[Model], func: MessageCallback) -> None:
        """
        Set the default message handler for the edge that will be overwritten if
        a decorator defines a new function to be called.
        """
        if self._model and self._model is not model:
            raise ValueError("Functionality already set with a different model!")
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
        def on_init(model: type[Model]):
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
        storage: StorageAPI | None = None,
        nodes: list[Node] | None = None,
        edges: list[Edge] | None = None,
        timeout: int = DEFAULT_SESSION_TIMEOUT_IN_SECONDS,
        version: str | None = None,
        cleanup_interval: int = 1,
    ) -> None:
        self._name = name
        self._nodes = nodes or []
        self._edges = edges or []
        self._graph: dict[str, list[str]] = self._build_graph()  # by nodes
        self._rules: dict[str, list[str]] = self._build_rules()  # by edges
        self._digest_by_edge: dict[str, str] = {
            edge.name: Model.build_schema_digest(edge.model) if edge.model else ""
            for edge in self._edges
        }  # store the message models that are associated with an edge

        self._starter = self._build_starter()  # first message of the dialogue
        self._ender = self._build_ender()  # last message(s) of the dialogue

        self._timeout = timeout
        self._storage: StorageAPI = storage or KeyValueStore(
            f"{self._name}_dialogue_storage"
        )  # persistent session + message storage
        self._sessions: dict[UUID, list[Any]] = (
            self._load_storage()
        )  # volatile session + message storage
        self._states: dict[
            UUID, str
        ] = {}  # current state of the dialogue (as edge digest) per session

        if self._sessions:
            self._states = {
                session_id: session[-1]["schema_digest"]
                for session_id, session in self._sessions.items()
            }

        super().__init__(name=self._name, version=version)

        # if a model exists for an edge, register the handler automatically
        self._auto_add_message_handler()

        self.initialise_cleanup_task(cleanup_interval)

        # radical but effective
        self.on_message = lambda *args, **kwargs: None  # type: ignore
        self.on_query = lambda *args, **kwargs: None  # type: ignore

    @property
    def rules(self) -> dict[str, list[str]]:
        """
        Property to access the rules of the dialogue.

        Returns:
            dict[str, list[str]]: Dictionary of rules represented by edges.
        """
        return self._rules

    @property
    def nodes(self) -> list[Node]:
        return self._nodes

    @property
    def edges(self) -> list[Edge]:
        return self._edges

    def get_overview(self) -> dict:
        """
        Get an overview of the dialogue structure.

        Returns:
            dict: Manifest like representation of the dialogue structure.
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

    def _build_graph(self) -> dict[str, list[str]]:
        """
        Build the graph of the dialogue while showing the state relations.

        Returns:
            dict[str, list[str]]: List of states and their relations.
        """
        graph = {}
        for node in self._nodes:
            graph.setdefault(node.name, [])
        for edge in self._edges:
            if edge.parent:
                graph.setdefault(edge.parent.name, []).append(edge.child.name)
        return graph

    def _build_rules(self) -> dict[str, list[str]]:
        """
        Build the rules for the dialogue.
        Which replies are allowed after a certain message.

        Returns:
            dict[str, list[str]]: Rules for the dialogue.
        """
        out = {edge.name: [] for edge in self._edges}
        for edge in self._edges:
            for inner_edge in self._edges:
                if inner_edge.parent and inner_edge.parent.name == edge.child.name:
                    out[edge.name].append(inner_edge.name)
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
                message="There is a starter node and an edge without parent present. "
                "The edge without a parent takes precedence!",
                category=SyntaxWarning,
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
        Return True if the digest is one of the last messages of the dialogue.
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

    def _pre_handle_hook(self, ctx: Context, sender: str, message: type[Model]) -> bool:
        schema_digest = Model.build_schema_digest(message)
        if not ctx.session:
            raise ValueError("Session ID must not be None!")
        is_valid = self.is_valid_message(ctx.session, schema_digest)
        if is_valid:
            if self.is_ender(schema_digest):
                self.update_state(schema_digest, ctx.session)
            self.add_message(
                session_id=ctx.session,
                message_type=self.models[schema_digest].__name__,
                schema_digest=schema_digest,
                sender=ctx.agent.address,
                receiver=sender,
                content=message.model_dump_json(),  # type: ignore
            )
        return is_valid

    def _post_handle_hook(self, ctx: Context, sender: str, msg_in: type[Model]) -> bool:
        if not ctx.session:
            raise ValueError("Session ID must not be None!")
        try:
            outbound_messages = ctx.outbound_messages  # type: ignore
        except AttributeError as exc:
            raise ValueError("Context must be an ExternalContext instance!") from exc

        if self.is_finished(ctx.session) or not outbound_messages:
            return True
        inbound_schema_digest = Model.build_schema_digest(msg_in)
        outbound_message_content, outbound_schema_digest = outbound_messages[sender][0]
        if not self.is_valid_reply(inbound_schema_digest, outbound_schema_digest):
            return False

        self.add_message(
            session_id=ctx.session,
            message_type=self.models[outbound_schema_digest].__name__,
            schema_digest=outbound_schema_digest,
            sender=ctx.agent.address,
            receiver=sender,
            content=outbound_message_content,
        )

        self.update_state(outbound_schema_digest, ctx.session)

        return True

    def _build_function_handler(self, edge: Edge) -> MessageCallback:
        if not edge.func:
            raise ValueError("No function handler set for edge!")

        @functools.wraps(edge.func)
        async def handler(ctx: Context, sender: str, message: type[Model]):
            # validate message first then execute handlers, finally update state
            if not self._pre_handle_hook(ctx, sender, message):
                return await ctx.send(
                    sender,
                    ErrorMessage(error=f"Unexpected message in dialogue: {message}"),
                )

            if edge.efunc:
                await edge.efunc(ctx, sender, message)
            result = await edge.func(ctx, sender, message)  # type: ignore

            if not self._post_handle_hook(ctx, sender, message):
                return MsgStatus(
                    status=DeliveryStatus.FAILED,
                    detail="Invalid dialogue reply",
                    destination=sender,
                    endpoint="",
                    session=ctx.session,
                )

            return result

        return handler  # type: ignore

    def _auto_add_message_handler(self) -> None:
        """Automatically add message handlers for edges with models."""
        for edge in self._edges:
            if edge.model and edge.func:
                self._add_message_handler(
                    model=edge.model,
                    func=self._build_function_handler(edge),
                    replies=None,  # no replies
                    allow_unverified=False,  # only verified
                )

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
        schema_digest: str,
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
                "schema_digest": schema_digest,
                "sender": sender,
                "receiver": receiver,
                "message_content": content,
                "timestamp": datetime.timestamp(datetime.now()),
                "timeout": self._timeout,
                **kwargs,
            }
        )
        self._update_session_in_storage(session_id)

    def get_conversation(
        self, session_id: UUID, message_filter: str | None = None
    ) -> list[Any]:
        """
        Return the message history of the given session from the dialogue instance as
        list of DialogueMessage.
        This includes both sent and received messages.

        Args:
            session_id (UUID): The ID of the session to get the conversation for.
            message_filter (str | None): The name of the message type to filter for

        Returns:
            list(DialogueMessage): A list of all messages exchanged during the given session
            list(DialogueMessage): Only messages of type 'message_filter' (Model.__name__)
            from the given session
        """
        conversation = self._sessions.get(session_id, [])
        if message_filter is None:
            return conversation

        return [
            message
            for message in conversation
            if message["message_type"] == message_filter
        ]

    def get_edge(self, edge_name: str) -> Edge:
        """Return an edge from the dialogue instance."""
        return next(edge for edge in self._edges if edge.name == edge_name)

    def _resolve_mapping(self, msg_digest: str) -> str:
        """Resolve the mapping of a message digest to a message model."""
        return next(k for k, v in self._digest_by_edge.items() if v == msg_digest)

    def is_valid_message(self, session_id: UUID, msg_digest: str) -> bool:
        """
        Check if an incoming message is valid for a given session.

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

    def _load_storage(self) -> dict[UUID, list[Any]]:
        """Load the sessions from the storage."""
        cache: dict | None = self._storage.get(self._name)
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
        cache: dict = self._storage.get(self.name) or {}
        session = str(session_id)
        if session in cache:
            cache.pop(session)
        self._storage.set(self.name, cache)

    def _update_transition_model(self, edge: Edge, model: type[Model]) -> None:
        """Update the message model for a transition."""
        self._digest_by_edge[edge.name] = Model.build_schema_digest(model)
        self._edges[self._edges.index(edge)].model = model

    def _on_state_transition(self, edge_name: str, model: type[Model]) -> Callable:
        """
        Main decorator to register a message handler for the dialogue.
        The Model in this case is the message model type but it refers to the
        Edge which is the transition between two states.

        Replies will not be validated based on the decorator parameters but
        on the graph and its rules instead.

        Args:
            edge (Edge): Edge object that represents the transition.
            model (type[Model]): Message model type.
        """
        if edge_name not in self._digest_by_edge:
            raise ValueError("Edge does not exist in the dialogue!")

        def decorator_on_state_transition(func: MessageCallback) -> MessageCallback:
            edge = self.get_edge(edge_name)
            edge.func = func
            handler = self._build_function_handler(edge)
            self._update_transition_model(edge, model)
            self._add_message_handler(model, handler, None, False)
            return handler

        return decorator_on_state_transition

    def manifest(self) -> dict[str, Any]:
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

    async def start_dialogue(
        self, ctx: Context, destination: str, message: Model
    ) -> list[MsgStatus]:
        """
        Start a dialogue with a message.

        Args:
            ctx (Context): The current message context
            destination (str): Either the agent address of the receiver or a protocol digest
            message (Model): The current message to send

        Raises:
            ValueError: If the dialogue is not started with the specified starting message.
        """
        message_schema_digest = Model.build_schema_digest(message)
        if not self.is_starter(message_schema_digest):
            raise ValueError(
                "A dialogue can only be started with the specified starting message"
            )

        status_list: list[MsgStatus] = []

        if destination.startswith("proto:"):
            status_list = await ctx.broadcast(destination, message)
        elif destination.startswith("agent"):
            status_list.append(await ctx.send(destination, message))
        else:
            raise ValueError("Invalid destination address")

        for status in status_list:
            if status.status == DeliveryStatus.FAILED:
                continue
            if status.session is None:
                raise ValueError("Session ID must not be None!")

            self.add_message(
                session_id=status.session,
                message_type=self.models[message_schema_digest].__name__,
                schema_digest=message_schema_digest,
                sender=ctx.agent.address,
                receiver=status.destination,
                content=message.model_dump_json(),
            )
            self.update_state(message_schema_digest, status.session)

        return status_list

    def initialise_cleanup_task(self, interval: int = 1) -> None:
        """
        Initialise the cleanup task.

        Deletes sessions that have not been used for a certain amount of time.
        The task runs every second so the configured timeout is currently
        measured in seconds as well (interval time * timeout parameter).
        Sessions with 0 as timeout will never be deleted.

        *Important*:
        - setting the interval above 1 will act as a multiplier
        - setting it to 0 will disable the cleanup task
        """
        if interval == 0:
            return

        @self.on_interval(interval)
        async def cleanup_dialogue(_ctx: Context):
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
