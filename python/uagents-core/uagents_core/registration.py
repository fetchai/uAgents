import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import AliasChoices, BaseModel, Field

from uagents_core.identity import Identity, parse_identifier
from uagents_core.types import AgentEndpoint, AgentInfo, AgentType


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


class AgentRegistrationAttestationBatch(BaseModel):
    attestations: list[AgentRegistrationAttestation]


class AgentProfile(BaseModel):
    description: str = Field(
        default="",
        max_length=300,
        description="Short description of the agent",
    )
    readme: str = Field(
        default="",
        max_length=80000,
        description="Detailed README for the agent",
    )
    avatar_url: str = Field(
        default="",
        max_length=4000,
        description="URL to the agent's avatar image",
    )


class RegistrationRequest(BaseModel):
    address: str = Field(
        ...,
        max_length=66,
        description="Agent's address (bech32 encoded public key with prefix 'agent')",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=80,
        description="Agent's public name",
    )
    handle: str | None = Field(
        None,
        max_length=40,
        description="Agent's unique handle",
    )
    url: str | None = Field(
        None,
        max_length=4000,
        description="Public URL for the agent",
    )
    agent_type: AgentType = Field(default="uagent", description="The type of the agent")
    profile: AgentProfile = AgentProfile()
    endpoints: list[AgentEndpoint] = Field(
        default=[], description="List of agent endpoints"
    )
    protocols: list[str] = Field(
        default=[], description="List of supported protocol digests"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata for the agent"
    )


class BatchRegistrationRequest(BaseModel):
    agents: list[RegistrationRequest] = Field(
        default=[], description="List of agents to register"
    )


class AgentverseConnectRequest(BaseModel):
    user_token: str
    agent_type: AgentType = "mailbox"
    endpoint: str | None = None
    team: str | None = None


class AgentverseDisconnectRequest(BaseModel):
    user_token: str
    team: str | None = None


class RegistrationResponse(BaseModel):
    success: bool


class ChallengeRequest(BaseModel):
    address: str


class ChallengeResponse(BaseModel):
    challenge: str


class IdentityProof(BaseModel):
    address: str = Field(
        ...,
        max_length=66,
        description="Agent's address (bech32 encoded public key with prefix 'agent')",
    )
    challenge: str
    challenge_response: str


class IdentityResponse(BaseModel):
    address: str = Field(
        ...,
        max_length=66,
        description="Agent's address (bech32 encoded public key with prefix 'agent')",
    )


class AgentUpdates(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    readme: str | None = Field(default=None, max_length=80000)
    avatar_url: str | None = Field(default=None, max_length=4000)
    short_description: str | None = Field(default=None, max_length=300)
    agent_type: str = "custom"


class AgentStatusUpdate(VerifiableModel):
    is_active: bool = Field(
        ..., description="Indicates whether the agent is currently active"
    )
