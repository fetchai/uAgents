import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import AliasChoices, BaseModel, Field

from uagents_core.identity import Identity, parse_identifier
from uagents_core.types import AddressPrefix, AgentEndpoint, AgentInfo, AgentType


class AgentRegistrationPolicy(ABC):
    @abstractmethod
    async def register(
        self,
        agent_identifier: str,
        identity: Identity,
        protocols: list[str],
        endpoints: list[AgentEndpoint],
        metadata: dict[str, Any] | None = None,
    ):
        raise NotImplementedError


class BatchRegistrationPolicy(ABC):
    @abstractmethod
    async def register(self):
        raise NotImplementedError

    @abstractmethod
    def add_agent(self, agent_info: AgentInfo, identity: Identity):
        raise NotImplementedError


# Registration models
class VerifiableModel(BaseModel):
    agent_identifier: str = Field(
        validation_alias=AliasChoices("agent_identifier", "agent_address")
    )
    signature: str | None = None
    timestamp: int | None = None

    def sign(self, identity: Identity) -> None:
        self.timestamp = int(time.time())
        digest = self._build_digest()
        self.signature = identity.sign_digest(digest)

    def verify(self) -> bool:
        _, _, agent_address = parse_identifier(self.agent_identifier)
        return self.signature is not None and Identity.verify_digest(
            address=agent_address,
            digest=self._build_digest(),
            signature=self.signature,
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


# AlmanacAPI related models
class AgentRegistrationAttestation(VerifiableModel):
    protocols: list[str]
    endpoints: list[AgentEndpoint]
    metadata: dict[str, str | list[str] | dict[str, str]] | None = None


# Agentverse related models
class RegistrationRequest(BaseModel):
    address: str
    prefix: AddressPrefix | None = "test-agent"
    challenge: str
    challenge_response: str
    agent_type: AgentType
    endpoint: str | None = None


class AgentverseConnectRequest(BaseModel):
    user_token: str
    agent_type: AgentType
    endpoint: str | None = None


class RegistrationResponse(BaseModel):
    success: bool


class ChallengeRequest(BaseModel):
    address: str


class ChallengeResponse(BaseModel):
    challenge: str


class AgentUpdates(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    readme: str | None = Field(default=None, max_length=80000)
    avatar_url: str | None = Field(default=None, max_length=4000)
    short_description: str | None = Field(default=None, max_length=300)
    agent_type: AgentType | None = "custom"


class AgentStatusUpdate(VerifiableModel):
    is_active: bool = Field(
        ..., description="Indicates whether the agent is currently active"
    )
