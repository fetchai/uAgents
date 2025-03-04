from logging import DEBUG

from protocol.search_protocol import (
    SearchRequest,
    SearchResponse,
)

from uagents import Agent, Context, Model
from uagents.types import AgentGeolocation

"""
Eventually, the search agent should be retrieved from the seach-engine by combining the
search protocol digest and a specific tag and/or search term to get the right type of search agent
"""
# SEARCH_AGENT = "agent1qw4yxv0uwh676038uu7ngf7kxp2ch82g7p20e8kcclaf6mg4y22ggll8kv8" # async
SEARCH_AGENT = (
    "agent1qvw7e5y0vu989xnek86t8c8qmeqgdmadjq83vu3t758thrfncv762ssgwax"  # sync
)

agent = Agent(
    name="my-searching-agent",
    port=8101,
    endpoint="http://localhost:8101/submit",
    log_level=DEBUG,
)


@agent.on_event("startup")
async def startup(ctx: Context):
    # TODO refactor search interface to take both protocol and text to find search agent
    # search_agent = search.search_agents_by_text
    ctx.logger.info(Model.build_schema_digest(SearchRequest))
    await ctx.send(
        SEARCH_AGENT,
        SearchRequest(
            query="",  # no effect in the current example setup
            tags=["evct"],  # no effect in the current example setup
            geolocation=AgentGeolocation(latitude=48.765, longitude=9.123, radius=5000),
            # attribute_filter={"charging": "yes"}, # should return only hit_agent
            attribute_filter={"colour": "blue"},  # should return both agents
            # attribute_filter={"swag": "max"}, # should return no agent
        ),
    )


@agent.on_message(SearchResponse)
async def handle_search_response(ctx: Context, sender: str, msg: SearchResponse):
    ctx.logger.info(f"search results: {msg.result_list}")


if __name__ == "__main__":
    agent.run()
