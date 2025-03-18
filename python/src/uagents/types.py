import logging
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)
from typing_extensions import Self
from uagents_core.envelope import Envelope
from uagents_core.models import Model

from uagents.config import (
    MESSAGE_HISTORY_MESSAGE_LIMIT,
    MESSAGE_HISTORY_RETENTION_SECONDS,
)
from uagents.storage import StorageAPI

if TYPE_CHECKING:
    from uagents.context import Context

JsonStr = str

IntervalCallback = Callable[["Context"], Awaitable[None]]
MessageCallback = Callable[["Context", str, Any], Awaitable[None]]
EventCallback = Callable[["Context"], Awaitable[None]]
WalletMessageCallback = Callable[["Context", Any], Awaitable[None]]

RestReturnType = dict[str, Any] | Model
RestGetHandler = Callable[["Context"], Awaitable[RestReturnType | None]]
RestPostHandler = Callable[["Context", Any], Awaitable[RestReturnType | None]]
RestHandler = RestGetHandler | RestPostHandler
RestMethod = Literal["GET", "POST"]
RestHandlerMap = dict[tuple[RestMethod, str], RestHandler]


AgentNetwork = Literal["mainnet", "testnet"]


class RestHandlerDetails(BaseModel):
    method: RestMethod
    endpoint: str
    request_model: type[Model] | None = None
    response_model: type[Model | BaseModel]


class AgentGeolocation(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False)
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    radius: Annotated[float, Field(gt=0)] = 0.5

    @field_validator("latitude", "longitude")
    @classmethod
    def serialize_precision(cls, val: float) -> float:
        """
        Round the latitude and longitude to 6 decimal places.
        Equivalent to 0.11m precision.
        """
        return round(val, 6)


class AgentMetadata(BaseModel):
    """
    Model used to validate metadata for an agent.

    Framework specific fields will be added here to ensure valid serialization.
    Additional fields will simply be passed through.
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )

    geolocation: AgentGeolocation | None = None


class MsgInfo(BaseModel):
    """
    Represents a message digest containing a message and its schema digest and sender.

    Attributes:
        message (Any): The message content.
        sender (str): The address of the sender of the message.
        schema_digest (str): The schema digest of the message.
    """

    message: Any
    sender: str
    schema_digest: str


class EnvelopeHistoryEntry(BaseModel):
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    version: int
    sender: str
    target: str
    session: UUID4
    schema_digest: str
    protocol_digest: str | None = None
    payload: str | None = None

    @field_serializer("session")
    def serialize_session(self, session: UUID4, _info) -> JsonStr:
        return str(session)

    @classmethod
    def from_envelope(cls, envelope: Envelope) -> Self:
        return cls(
            version=envelope.version,
            sender=envelope.sender,
            target=envelope.target,
            session=envelope.session,
            schema_digest=envelope.schema_digest,
            protocol_digest=envelope.protocol_digest,
            payload=envelope.decode_payload(),
        )


class EnvelopeHistoryResponse(BaseModel):
    envelopes: list[EnvelopeHistoryEntry]


class SessionHistoryInfo(BaseModel):
    latest_timestamp: int
    message_count: int


class EnvelopeHistory:
    """
    Stores message history for an agent optionally using cache and/or storage.
    """

    def __init__(
        self,
        storage: StorageAPI,
        use_cache: bool = True,
        use_storage: bool = False,
        logger: logging.Logger | None = None,
        retention_period: int = MESSAGE_HISTORY_RETENTION_SECONDS,
        message_limit: int = MESSAGE_HISTORY_MESSAGE_LIMIT,
    ) -> None:
        """
        Initialize the message history.

        Args:
            storage (StorageAPI): The storage API to use.
            use_cache (bool): Whether to use the cache.
            use_storage (bool): Whether to use the storage.
            logger (logging.Logger | None): The logger to use.
            retention_period (int): The retention period in seconds.
            message_limit (int): The message limit.
        """
        self._cache: list[EnvelopeHistoryEntry] | None = [] if use_cache else None
        self._storage: StorageAPI | None = storage if use_storage else None
        self._logger = logger or logging.getLogger(__name__)
        self._retention_period = retention_period
        self._message_limit = message_limit

    def add_entry(self, entry: EnvelopeHistoryEntry) -> None:
        """
        Add an envelope entry to the message history.

        Args:
            entry (EnvelopeHistoryEntry): The entry to add.
        """
        if self._cache is not None:
            self._cache.append(entry)
        if self._storage is not None:
            key = self._get_key(entry.session)
            session_msgs: list[JsonStr] = self._storage.get(key) or []
            try:
                session_info = SessionHistoryInfo(
                    latest_timestamp=entry.timestamp,
                    message_count=len(session_msgs) + 1,
                )
                self._update_session_info(entry.session, session_info)
                session_msgs.append(entry.model_dump_json())
                self._storage.set(key, session_msgs)
            except RuntimeError as ex:
                self._logger.error(f"{ex.args[0]} Message will not be stored.")
        self.apply_retention_policy()

    def _update_session_info(
        self, session: UUID4, info_update: SessionHistoryInfo
    ) -> None:
        if self._storage is not None:
            all_sessions = self._storage.get("message-history:sessions") or {}
            total_msgs = 0
            for info_json in all_sessions.values():
                info = SessionHistoryInfo.model_validate_json(info_json)
                total_msgs += info.message_count
            if total_msgs >= self._message_limit:
                raise RuntimeError("Message history storage limit exceeded!")
            all_sessions.update({str(session): info_update.model_dump_json()})
            self._storage.set("message-history:sessions", all_sessions)

    def _get_key(self, session: UUID4 | str) -> str:
        return f"message-history:session:{str(session)}"

    def get_cached_messages(self) -> EnvelopeHistoryResponse:
        """
        Retrieve the cached message history.

        Returns:
            EnvelopeHistoryResponse: The cached message history.
        """
        if self._cache is None:
            raise ValueError("EnvelopeHistory cache is not set")
        return EnvelopeHistoryResponse(envelopes=self._cache)

    def get_session_messages(self, session: UUID4) -> list[EnvelopeHistoryEntry]:
        """
        Retrieve the message history for a given session.

        Args:
            session (UUID4): The session UUID.

        Returns:
            list[EnvelopeHistoryEntry]: The message history for the session.
        """
        if self._storage is None:
            raise ValueError("EnvelopeHistory storage is not set")
        session_msgs = self._storage.get(self._get_key(session)) or []
        return [EnvelopeHistoryEntry.model_validate_json(msg) for msg in session_msgs]

    def apply_retention_policy(self) -> None:
        """Remove entries older than retention period."""
        cutoff_time = time.time() - self._retention_period

        # apply retention policy to cache
        if self._cache is not None:
            for e in self._cache:
                if e.timestamp < cutoff_time:
                    self._cache.remove(e)
                else:
                    break
            if len(self._cache) > self._message_limit:
                self._cache = self._cache[-self._message_limit :]

        # apply retention policy to storage
        if self._storage is not None:
            all_sessions = self._storage.get("message-history:sessions") or {}
            sessions_to_remove = []
            for session, info_json in all_sessions.items():
                info = SessionHistoryInfo.model_validate_json(info_json)
                if info.latest_timestamp < cutoff_time:
                    self._storage.remove(self._get_key(session))
                    sessions_to_remove.append(session)
            for session in sessions_to_remove:
                del all_sessions[session]

            self._storage.set("message-history:sessions", all_sessions)
