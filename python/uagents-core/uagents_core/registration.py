import hashlib
import json
import time
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from uagents_core.crypto import Identity
from uagents_core.types import AddressPrefix, AgentEndpoint, AgentType
from uagents_core.utils.communication import parse_identifier


class VerifiableModel(BaseModel):
    agent_identifier: str
    signature: Optional[str] = None
    timestamp: Optional[int] = None

    def sign(self, identity: Identity):
        self.timestamp = int(time.time())
        digest = self._build_digest()
        self.signature = identity.sign_digest(digest)

    def verify(self) -> bool:
        _, _, agent_address = parse_identifier(self.agent_identifier)
        return self.signature is not None and Identity.verify_digest(
            agent_address, self._build_digest(), self.signature
        )

    def _build_digest(self) -> bytes:
        sha256 = hashlib.sha256()
        sha256.update(
            json.dumps(
                self.model_dump(exclude={"signature"}),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        return sha256.digest()


class AgentRegistrationAttestation(VerifiableModel):
    protocols: List[str]
    endpoints: List[AgentEndpoint]
    metadata: Optional[Dict[str, Union[str, Dict[str, str]]]] = None


class RegistrationRequest(BaseModel):
    address: str
    prefix: Optional[AddressPrefix] = "test-agent"
    challenge: str
    challenge_response: str
    agent_type: AgentType
    endpoint: Optional[str] = None


class AgentverseConnectRequest(BaseModel):
    user_token: str
    agent_type: AgentType
    endpoint: Optional[str] = None


class RegistrationResponse(BaseModel):
    success: bool


class ChallengeRequest(BaseModel):
    address: str


class ChallengeResponse(BaseModel):
    challenge: str


class AgentUpdates(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    readme: Optional[str] = Field(default=None, max_length=80000)
    avatar_url: Optional[str] = Field(default=None, max_length=4000)
    agent_type: Optional[AgentType] = "custom"
