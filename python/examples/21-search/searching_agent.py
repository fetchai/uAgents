from logging import DEBUG

from protocol.search_protocol import (
    SearchRequest,
    SearchResponse,
)

from uagents import Agent, Context, Model
from uagents.types import AgentGeolocation

SEARCH_AGENT = "agent1qw4yxv0uwh676038uu7ngf7kxp2ch82g7p20e8kcclaf6mg4y22ggll8kv8"

agent = Agent(
    name="my-searching-agent",
    port=8101,
    endpoint="localhost:8101/submit",
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
            query="uniquechargingquery",
            tags=["evct"],
            geolocation=AgentGeolocation(latitude=48.765, longitude=9.123, radius=5000),
            attribute_filter={"charging": "yes"},
        ),
    )


@agent.on_message(SearchResponse)
async def handle_search_response(ctx: Context, sender: str, msg: SearchResponse):
    ctx.logger.info(f"search results: {msg.result_list}")


if __name__ == "__main__":
    agent.run()
