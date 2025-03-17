"""Agent Envelope."""

import base64
import hashlib
import logging
import struct
import time
from collections.abc import Callable

from pydantic import UUID4, BaseModel, Field, field_serializer
from typing_extensions import Self

from uagents.config import (
    MESSAGE_HISTORY_MESSAGE_LIMIT,
    MESSAGE_HISTORY_RETENTION_SECONDS,
)
from uagents.crypto import Identity
from uagents.storage import StorageAPI
from uagents.types import JsonStr


class Envelope(BaseModel):
    """
    Represents an envelope for message communication between agents.

    Attributes:
        version (int): The envelope version.
        sender (str): The sender's address.
        target (str): The target's address.
        session (UUID4): The session UUID that persists for back-and-forth
        dialogues between agents.
        schema_digest (str): The schema digest for the enclosed message.
        protocol_digest (str | None): The digest of the protocol associated with the message
        (optional).
        payload (str | None): The encoded message payload of the envelope (optional).
        expires (int | None): The expiration timestamp (optional).
        nonce (int | None): The nonce value (optional).
        signature (str | None): The envelope signature (optional).
    """

    version: int
    sender: str
    target: str
    session: UUID4
    schema_digest: str
    protocol_digest: str | None = None
    payload: str | None = None
    expires: int | None = None
    nonce: int | None = None
    signature: str | None = None

    def encode_payload(self, value: JsonStr) -> None:
        """
        Encode the payload value and store it in the envelope.

        Args:
            value (JsonStr): The payload value to be encoded.
        """
        self.payload = base64.b64encode(value.encode()).decode()

    def decode_payload(self) -> str:
        """
        Decode and retrieve the payload value from the envelope.

        Returns:
            str: The decoded payload value, or '' if payload is not present.
        """
        if self.payload is None:
            return ""

        return base64.b64decode(self.payload).decode()

    def sign(self, signing_fn: Callable) -> None:
        """
        Sign the envelope using the provided signing function.

        Args:
            signing_fn (callback): The callback used for signing.
        """
        try:
            self.signature = signing_fn(self._digest())
        except Exception as err:
            raise ValueError(f"Failed to sign envelope: {err}") from err

    def verify(self) -> bool:
        """
        Verify the envelope's signature.

        Returns:
            bool: True if the signature is valid.

        Raises:
            ValueError: If the signature is missing.
            ecdsa.BadSignatureError: If the signature is invalid.
        """
        if self.signature is None:
            raise ValueError("Envelope signature is missing")
        return Identity.verify_digest(self.sender, self._digest(), self.signature)

    def _digest(self) -> bytes:
        """
        Compute the digest of the envelope's content.

        Returns:
            bytes: The computed digest.
        """
        hasher = hashlib.sha256()
        hasher.update(self.sender.encode())
        hasher.update(self.target.encode())
        hasher.update(str(self.session).encode())
        hasher.update(self.schema_digest.encode())
        if self.payload is not None:
            hasher.update(self.payload.encode())
        if self.expires is not None:
            hasher.update(struct.pack(">Q", self.expires))
        if self.nonce is not None:
            hasher.update(struct.pack(">Q", self.nonce))
        return hasher.digest()


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
    ):
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
