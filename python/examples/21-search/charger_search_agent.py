import uuid
from datetime import datetime, timedelta
from logging import DEBUG

from protocol.search_protocol import (
    AttributeQuery,
    AttributeResponse,
    SearchRequest,
    SearchResponse,
)

# from fetchai import fetch
from uagents import Agent, Context, Protocol
from uagents.experimental import search

# search scenarios (beyond basic search engine search)
# find agents where attribute == value
# find agents where attribute in range(min, max) / [val_1, ..., val_n]
# find agent where attribute is highest/lowest limit num_of_choices

MY_TIMEOUT = 10

agent = Agent(
    name="Search Agent for EV Chargers",
    # seed = "<put unique seed>",
    port=8100,
    endpoint="http://localhost:8100/submit",
    agentverse="https://staging.agentverse.ai",
    log_level=DEBUG,
)

search_proto = Protocol(name="agent-search-protocol", version="0.1.0")


@search_proto.on_message(SearchRequest)
async def handle_search_request(ctx: Context, sender: str, msg: SearchRequest):
    ctx.logger.info(f"Received search request from {sender}")
    # create a new session to eventually link incoming responses to the original caller
    search_session = uuid.uuid4()
    storage_dict = {
        str(search_session): {
            "searcher": sender,
            "timeout": str(datetime.now() + timedelta(seconds=MY_TIMEOUT)),
            "request": msg.model_dump_json(),
            "responses": {},
        }
    }
    sessions = ctx.storage.get("sessions") or {}
    sessions.update(storage_dict)
    ctx.storage.set("sessions", sessions)

    ctx.logger.info(f"starting new session {search_session} for agent {sender}")

    agents = search.geosearch_agents_by_text(
        latitude=msg.geolocation.latitude,
        longitude=msg.geolocation.longitude,
        radius=msg.geolocation.radius,
        search_text=msg.query,
    )

    query = AttributeQuery(
        search_id=search_session, attributes=list(msg.attribute_filter)
    )

    for agent in agents:
        ctx.logger.info(f"querying agent: {agent.address}")
        await ctx.send(agent.address, query)

    ## broadcast currently doesn't allow for additional filters, so it might reach agents
    ## that wouldn't be returned by the search engine (e.g., outside of geo search area)
    # ctx.broadcast(msg.protocol_digest, query)
    ## this could be a convenience function to wrap the above loop internally
    # ctx.broadcast(msg.protocol_digest, query, msg.query, msg.geolocation, msg.tags)


@agent.on_message(AttributeResponse)
async def handle_attribute_response(ctx: Context, sender: str, msg: AttributeResponse):
    """
    Collect responses and map them to the corresponding search sessions so they can be handled
    in bulk after session timeout
    """
    sessions = ctx.storage.get("sessions")
    if msg.attributes is None or len(msg.attributes) == 0:
        ctx.logger.info(f"no matching attribute from agent {sender[:8]}...")
        return

    if not msg.search_id or str(msg.search_id) not in sessions:
        ctx.logger.info("AttributeResponse for unknown search_id")
        return

    # if the agent features the queried attribute, include it in the responses
    ctx.logger.info(f"Got a matching response from agent {sender[:8]}...")
    responses = sessions[str(msg.search_id)]["responses"]
    response = {sender: msg.attributes}
    responses.update(response)
    ctx.storage.set("sessions", sessions)


@agent.on_interval(6)
async def check_queries(ctx: Context):
    """Check for each active session, if timeout is reached. If so finish the corresponding query"""
    sessions_sync = ctx.storage.get("sessions") or {}
    sessions = sessions_sync.copy()
    ctx.logger.info(f"active sessions: {len(sessions)}")
    if len(sessions) > 0:
        for session, session_info in sessions.items():
            if datetime.fromisoformat(session_info["timeout"]) < datetime.now():
                ctx.logger.info(f"finish session {session}")
                await finish_query(ctx, session)


async def finish_query(ctx: Context, session: str):
    """
    Collect all responses and only return those agents that match the search terms of the
    initial request
    """
    sessions = ctx.storage.get("sessions")
    session_info = sessions.pop(session)
    ctx.storage.set("sessions", sessions)
    matching_agents = []
    # evaluate all replies given the initial query
    for agent, attributes in session_info["responses"].items():
        # parse into model for better handling
        search_request = SearchRequest.model_validate_json(session_info["request"])
        # for a first test simply check attribute equality
        for attribute, value in search_request.attribute_filter.items():
            if attributes[attribute] == value:
                matching_agents.append(agent)
    await ctx.send(
        session_info["searcher"], SearchResponse(result_list=matching_agents)
    )


agent.include(search_proto)

if __name__ == "__main__":
    agent.run()
