from a2a.types import AgentCard
from uagents_core.agentverse.sdk.common.av import CHAT_PROTOCOL
from uagents_core.agentverse.sdk.common.config import (
    DEFAULT_AGENTVERSE_CHAT_ENDPOINT,
)
from uagents_core.agentverse.sdk.common.types import AgentverseAgent
from uagents_core.registration import AgentProfile, RegistrationRequest
from uagents_core.types import AgentEndpoint


def _generate_readme(card: AgentCard) -> str:
    title = (
        f"{card.name} by {card.provider.organization}"
        if card.provider is not None
        else card.name
    )

    skills = []

    for skill in card.skills:
        examples = (
            "Examples\n" + "\n\n".join([f"- `{eg}`" for eg in skill.examples])
            if skill.examples is not None
            else None
        )
        skills.append(f"### {skill.name}\n{skill.description}\n\n{examples or ''}")
    skills = "\n".join(skills)

    about = (
        f"Learn more about [{card.name}]({card.documentation_url})."
        if card.documentation_url is not None
        else ""
    )
    about += (
        f"\n\nLearn more about [{card.provider.organization}]({card.provider.url})."
        if card.provider is not None
        else ""
    )
    about = f"## About\n{about}" if about else ""

    readme = f"""
# {title}
{card.description}

## What this agent can do (Skills)

{skills}


{about}
            """

    return readme


def _generate_registration_request(
    agent: AgentverseAgent, card: AgentCard | None = None
) -> RegistrationRequest:

    request = RegistrationRequest(
        address=agent.uri.identity.address,
        name=agent.uri.name,
        handle=agent.uri.handle,
        agent_type="a2a",
        profile=agent.profile or AgentProfile(),
        metadata=agent.metadata,
    )

    if card:
        request.url = card.documentation_url
        chat_url = (
            f"{card.url.strip('/')}/{DEFAULT_AGENTVERSE_CHAT_ENDPOINT.strip('/')}"
        )
        request.endpoints = [AgentEndpoint(url=chat_url, weight=1)]
        request.protocols = [CHAT_PROTOCOL]

        if not request.profile.description:
            request.profile.description = card.description
        if not request.profile.readme:
            request.profile.readme = _generate_readme(card)
        if not request.profile.avatar_url:
            request.profile.avatar_url = card.icon_url

    return request
