"""Testing agent."""

from uagents import Agent, Context

from project.models.agent_com import LlmResponse, RequestData

RECIPIENT_ADDRESS = "address_of_the_agent_to_send_the_message_to"

sigmar = Agent(
    name="project",
    seed="insert_your_seed_here",
    port=8081,
    endpoint="http://localhost:8081/submit",
)


@sigmar.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Agent started")
    ctx.storage.set("index", 0)


@sigmar.on_message(model=LlmResponse)
async def message_handler(ctx: Context, sender: str, msg: LlmResponse):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


@sigmar.on_interval(period=10.0)
async def send_message(ctx: Context):
    """Main agent logic."""
    index = ctx.storage.get("index") or 0

    prompt = None
    if index == 0:
        prompt = "How many agents do you have?"
    elif index == 1:
        prompt = "Give me all agent names, please."
    elif index == 2:  # noqa
        prompt = "How many mailboxes do you have?"
    elif index == 3:  # noqa
        prompt = "How many users do you have?"
    elif index == 4:  # noqa
        prompt = "Which agents have no description?"

    if prompt:
        await ctx.send(RECIPIENT_ADDRESS, RequestData(prompt=prompt))
        index += 1
        ctx.storage.set("index", index)


if __name__ == "__main__":
    sigmar.run()
