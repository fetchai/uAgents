import base64
import hashlib
import json
from typing import Optional, Any

from pydantic import BaseModel, UUID4

from nexus.crypto import Identity


class Envelope(BaseModel):
    version: int
    sender: str
    target: str
    session: UUID4
    protocol: str
    payload: Optional[str] = None
    signature: Optional[str] = None

    def encode_payload(self, value: Any):
        self.payload = base64.b64encode(json.dumps(value).encode()).decode()

    def decode_payload(self) -> Optional[Any]:
        if self.payload is None:
            return None

        return json.loads(base64.b64decode(self.payload).decode())

    def sign(self, identity: Identity):
        self.signature = identity.sign_digest(self._digest())

    def verify(self) -> bool:
        if self.signature is None:
            return False

        return Identity.verify_digest(self.sender, self._digest(), self.signature)

    def _digest(self) -> bytes:
        hasher = hashlib.sha256()
        hasher.update(self.sender.encode())
        hasher.update(self.target.encode())
        hasher.update(str(self.session).encode())
        hasher.update(self.protocol.encode())
        if self.payload is not None:
            hasher.update(self.payload.encode())
        return hasher.digest()
