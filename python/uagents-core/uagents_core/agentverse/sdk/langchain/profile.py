from uagents_core.agentverse.sdk.common.av import CHAT_PROTOCOL
from uagents_core.agentverse.sdk.common.types import AgentverseAgent
from uagents_core.agentverse.sdk.langchain.config import LangGraphAdapterConfig
from uagents_core.registration import AgentProfile, RegistrationRequest
from uagents_core.types import AgentEndpoint


def _combine_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _generate_readme(
    agent: AgentverseAgent,
    config: LangGraphAdapterConfig,
    public_url: str,
) -> str:
    chat_url = _combine_url(public_url, config.chat_endpoint)

    return f"""# {agent.uri.name}
LangGraph agent bridged to Agentverse.

## What this agent can do
- Receive Agentverse chat messages at `{config.chat_endpoint}`
- Forward incoming text to LangGraph assistant `{config.assistant_id}`
- Return the model response back through the Agentverse chat protocol

## Endpoints
- Base URL: {public_url}
- Chat endpoint: {chat_url}
"""


def _generate_registration_request(
    agent: AgentverseAgent,
    config: LangGraphAdapterConfig,
    public_url: str,
) -> RegistrationRequest:
    identity = agent.uri.identity

    profile_data = agent.profile.model_dump() if agent.profile is not None else {}
    profile = AgentProfile(**profile_data)

    if not profile.description:
        profile.description = (
            f"LangGraph agent '{config.assistant_id}' bridged to Agentverse."
        )

    if not profile.readme:
        profile.readme = _generate_readme(agent, config, public_url)

    request = RegistrationRequest(
        address=identity.address,
        name=agent.uri.name,
        handle=agent.uri.handle,
        agent_type="uagent",
        profile=profile,
        metadata=agent.metadata,
    )

    request.url = public_url
    request.endpoints = [
        AgentEndpoint(
            url=_combine_url(public_url, config.chat_endpoint),
            weight=1,
        )
    ]
    request.protocols = [CHAT_PROTOCOL]

    return request
