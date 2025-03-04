import uuid
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


agent = Agent(
    name="Search Agent for EV Chargers sync",
    # seed = "<put unique seed>",
    port=8099,
    endpoint="http://localhost:8099/submit",
    agentverse="https://staging.agentverse.ai",
    log_level=DEBUG,
)

search_proto = Protocol(name="agent-search-protocol", version="0.1.0")


@search_proto.on_message(SearchRequest)
async def handle_search_request(ctx: Context, sender: str, msg: SearchRequest):
    ctx.logger.info(f"Received search request from {sender}")
    # create a new session to eventually link incoming responses to the original caller
    search_session = uuid.uuid4()
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

    responses = {}
    for agent in agents:
        ctx.logger.info(f"querying agent: {agent.address}")
        reply: AttributeResponse
        reply, status = await ctx.send_and_receive(
            agent.address, query, response_type=AttributeResponse
        )
        if not isinstance(reply, AttributeResponse):
            ctx.logger.info(f"Received unexpected response from {agent.address[:8]}..")
            continue

        if reply.attributes is None or len(reply.attributes) == 0:
            ctx.logger.info(f"no matching attribute from agent {agent.address[:8]}...")
            continue

        if not reply.search_id or reply.search_id != search_session:
            ctx.logger.info("AttributeResponse for unknown search_id")
            continue

        # if the agent features the queried attribute, include it in the responses
        ctx.logger.info(f"Got a matching response from agent {agent.address[:8]}...")
        responses.update({agent.address: reply.attributes})

    matching_agents = []
    # evaluate all replies given the initial query
    for agent, attributes in responses.items():
        # for a first test simply check attribute equality
        for attribute, value in msg.attribute_filter.items():
            if attributes[attribute] == value:
                matching_agents.append(agent)
    await ctx.send(sender, SearchResponse(result_list=matching_agents))


agent.include(search_proto)

if __name__ == "__main__":
    agent.run()
