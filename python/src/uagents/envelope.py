"""Agent Envelope."""

import base64
import hashlib
import struct
import time
from typing import Callable, List, Optional

from pydantic import (
    UUID4,
    BaseModel,
    Field,
    field_serializer,
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
        protocol_digest (Optional[str]): The digest of the protocol associated with the message
        (optional).
        payload (Optional[str]): The encoded message payload of the envelope (optional).
        expires (Optional[int]): The expiration timestamp (optional).
        nonce (Optional[int]): The nonce value (optional).
        signature (Optional[str]): The envelope signature (optional).
    """

    version: int
    sender: str
    target: str
    session: UUID4
    schema_digest: str
    protocol_digest: Optional[str] = None
    payload: Optional[str] = None
    expires: Optional[int] = None
    nonce: Optional[int] = None
    signature: Optional[str] = None

    def encode_payload(self, value: JsonStr):
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

    def sign(self, signing_fn: Callable):
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
    protocol_digest: Optional[str] = None
    payload: Optional[str] = None

    @field_serializer("session")
    def serialize_session(self, session: UUID4, _info):
        return str(session)

    @classmethod
    def from_envelope(cls, envelope: Envelope):
        return cls(
            version=envelope.version,
            sender=envelope.sender,
            target=envelope.target,
            session=envelope.session,
            schema_digest=envelope.schema_digest,
            protocol_digest=envelope.protocol_digest,
            payload=envelope.decode_payload(),
        )


class EnvelopeHistory(BaseModel):
    cache: Optional[List[EnvelopeHistoryEntry]] = None
    storage: Optional[StorageAPI] = None

    def add_entry(self, entry: EnvelopeHistoryEntry):
        if self.cache is not None:
            self.cache.append(entry)
        if self.storage is not None:
            key = f"message-history:session:{entry.session}"
            session_msgs: List[EnvelopeHistoryEntry] = self.storage.get(key) or []
            session_msgs.append(entry)
            self.storage.set(key, session_msgs)

            # keep index of all sessions for retention policy
            all_sessions = self.storage.get("message-history:sessions") or []
            all_sessions.append(entry.session)
            self.storage.set("message-history:sessions", all_sessions)
        self.apply_retention_policy()

    def get_session_messages(self, session: UUID4) -> List[EnvelopeHistoryEntry]:
        if self.storage is None:
            raise ValueError("EnvelopeHistory storage is not set")
        key = f"message-history:session:{session}"
        return self.storage.get(key) or []

    def apply_retention_policy(self):
        """Remove entries older than 24 hours"""
        cutoff_time = time.time() - 86400

        # apply retention policy to cache
        if self.cache is not None:
            for e in self.cache:
                if e.timestamp < cutoff_time:
                    self.cache.remove(e)
                else:
                    break

        # apply retention policy to storage
        if self.storage is not None:
            all_sessions: List[str] = self.storage.get("message-history:sessions") or []
            for session in all_sessions:
                key = f"message-history:session:{session}"
                session_msgs: List[EnvelopeHistoryEntry] = self.storage.get(key) or []
                if session_msgs and session_msgs[-1].timestamp < cutoff_time:
                    self.storage.remove(key)
