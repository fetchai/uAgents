"""Agent Envelope."""

import base64
import hashlib
import struct
from typing import Optional, Any

from pydantic import BaseModel, Field, UUID4

from uagents.crypto import Identity
from uagents.dispatch import JsonStr


class Envelope(BaseModel):
    """
    Represents an envelope for message communication between agents.

    Attributes:
        version (int): The envelope version.
        sender (str): The sender's address.
        target (str): The target's address.
        session (UUID4): The session UUID that persists for back-and-forth
        dialogues between agents.
        schema_digest (str): The schema digest for the enclosed message (alias for protocol).
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
    schema_digest: str = Field(alias="protocol")
    protocol_digest: Optional[str] = None
    payload: Optional[str] = None
    expires: Optional[int] = None
    nonce: Optional[int] = None
    signature: Optional[str] = None

    class Config:
        allow_population_by_field_name = True

    def encode_payload(self, value: JsonStr):
        """
        Encode the payload value and store it in the envelope.

        Args:
            value (JsonStr): The payload value to be encoded.
        """
        self.payload = base64.b64encode(value.encode()).decode()

    def decode_payload(self) -> Optional[Any]:
        """
        Decode and retrieve the payload value from the envelope.

        Returns:
            Optional[Any]: The decoded payload value, or None if payload is not present.
        """
        if self.payload is None:
            return None

        return base64.b64decode(self.payload).decode()

    def sign(self, identity: Identity):
        """
        Sign the envelope using the provided identity.

        Args:
            identity (Identity): The identity used for signing.
        """
        self.signature = identity.sign_digest(self._digest())

    def verify(self) -> bool:
        """
        Verify the envelope's signature.

        Returns:
            bool: True if the signature is valid, False otherwise.
        """
        if self.signature is None:
            return False

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
