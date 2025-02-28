from protocol.search_protocol import AttributeQuery, AttributeResponse

from uagents import Context
from uagents.experimental.mobility import MobilityAgent
from uagents.types import AgentGeolocation

SEARCH_AGENT = ""
MY_ATTRIBUTES = {"charging": "no", "food": "yes", "colour": "red"}

agent = MobilityAgent(
    name="uniquechargingquery miss",
    port=8103,
    endpoint="localhost:8103/submit",
    location=AgentGeolocation(latitude=48.77, longitude=9.11, radius=2),
    mobility_type="vehicle",  # completely irrelevant for demo
    static_signal="food truck",
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
    await ctx.send(sender, AttributeResponse(attributes=attribute_values))


if __name__ == "__main__":
    agent.run()
