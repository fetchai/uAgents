import contextlib
import json
import traceback

from requests import HTTPError
from uagents_core.adapters.common.agentverse import (
    _post_data_sync,
    generate_agent_auth_token,
)
from uagents_core.adapters.common.logger import logger
from uagents_core.adapters.common.types import (
    AgentBatchEvents,
    AgentStarletteState,
    AgentUri,
)

FAILED_INIT_ERROR_FORMAT = "Failed to initialize agentverse sdk ({})"


def get_agent_address(agent: str | AgentUri) -> str | None:
    if isinstance(agent, str):
        try:
            agent = AgentUri.from_str(agent)
        except Exception:
            return None

    return agent.identity.address


def dispatch_event(agent: AgentUri | AgentStarletteState, events: AgentBatchEvents):
    _post_data_sync(
        url=f"{agent.agentverse.url}/v1/events",
        data=events,
        headers={"Authorization": f"Agent {generate_agent_auth_token(agent.identity)}"},
    )


@contextlib.contextmanager
def handle_init_errors(uri: AgentUri):
    try:
        yield
    except Exception as e:
        event = AgentBatchEvents.from_exception(e, traceback.format_exc())
        try:
            dispatch_event(uri, event)
        except HTTPError as dispatch_exception:
            logger.error(
                FAILED_INIT_ERROR_FORMAT.format(dispatch_exception.response.status_code)
            )  # TODO(LR): make sure timestamps are included in logger formatting
            logger.error(dispatch_exception.response.text)
        except Exception as generic_exception:
            logger.error(FAILED_INIT_ERROR_FORMAT.format(str(generic_exception)))
