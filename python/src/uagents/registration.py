import hashlib
import json
from typing import List, Optional

from pydantic import BaseModel
from uagents.config import AgentEndpoint
from uagents.crypto import Identity


class AgentRegistrationAttestation(BaseModel):
    agent_address: str
    protocols: List[str]
    endpoints: List[AgentEndpoint]
    signature: Optional[str] = None

    def sign(self, identity: Identity):
        digest = self._build_digest()
        self.signature = identity.sign_digest(digest)

    def verify(self) -> bool:
        if self.signature is None:
            return False
        return Identity.verify_digest(
            self.agent_address, self._build_digest(), self.signature
        )

    def _build_digest(self) -> bytes:
        normalised_attestation = AgentRegistrationAttestation(
            agent_address=self.agent_address,
            protocols=sorted(self.protocols),
            endpoints=sorted(self.endpoints, key=lambda x: x.url),
        )

        sha256 = hashlib.sha256()
        sha256.update(
            json.dumps(
                normalised_attestation.model_dump(exclude={"signature"}),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        return sha256.digest()