from protocol.search_protocol import AttributeQuery, AttributeResponse

from uagents import Context
from uagents.experimental.mobility import MobilityAgent
from uagents.types import AgentGeolocation

SEARCH_AGENT = ""
MY_ATTRIBUTES = {"charging": "yes", "food": "no", "colour": "blue"}
# TODO add agentverse registration so readme can get uploaded
agent = MobilityAgent(
    name="uniquechargingquery hit",
    port=8102,
    endpoint="http://localhost:8102/submit",
    location=AgentGeolocation(latitude=48.76, longitude=9.12, radius=2),
    mobility_type="vehicle",  # completely irrelevant for demo
    static_signal="charger",
)


@agent.on_message(AttributeQuery)
async def handle_search_response(ctx: Context, sender: str, msg: AttributeQuery):
    attribute_values = {}
    for attribute in msg.attributes:
        if attribute in MY_ATTRIBUTES:
            ctx.logger.info(f"query contains matching attribute: {attribute}")
            attribute_values.update({attribute: MY_ATTRIBUTES[attribute]})
        else:
            ctx.logger.info(f"query contains unknown attribute: {attribute}")
    await ctx.send(
        sender, AttributeResponse(search_id=msg.search_id, attributes=attribute_values)
    )


if __name__ == "__main__":
    agent.run()
