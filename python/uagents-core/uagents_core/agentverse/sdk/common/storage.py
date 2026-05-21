from uagents_core.agentverse.sdk.common.types import AgentContext, AgentverseAgent
from uagents_core.storage import ExternalStorage


def setup_agent_storage(ctx: AgentContext, agent: AgentverseAgent) -> ExternalStorage | None:
    """Configure ``ctx.storage`` for delegated asset uploads when enabled on the agent.

    Delegation to create storage assets must already be granted by the user.
    """
    if not agent.options.enable_storage:
        return None

    storage = ExternalStorage(
        identity=agent.uri.identity,
        storage_url=agent.uri.agentverse.storage_api,
    )
    ctx.storage = storage

    return storage
