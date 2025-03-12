"""Agent Envelope."""

import base64
import hashlib
import struct
import time
from collections.abc import Callable

from pydantic import UUID4, BaseModel, Field, field_serializer
from typing_extensions import Self
from uagents.crypto import Identity
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
        return Identity.verify_digest(
            address=self.sender, digest=self._digest(), signature=self.signature
        )

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


class EnvelopeHistory(BaseModel):
    envelopes: list[EnvelopeHistoryEntry]

    def add_entry(self, entry: EnvelopeHistoryEntry) -> None:
        self.envelopes.append(entry)
        self.apply_retention_policy()

    def apply_retention_policy(self) -> None:
        """Remove entries older than 24 hours"""
        cutoff_time = time.time() - 86400
        for e in self.envelopes:
            if e.timestamp < cutoff_time:
                self.envelopes.remove(e)
            else:
                break
