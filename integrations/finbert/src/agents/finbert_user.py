from uagents import Agent, Context, Protocol  # Import necessary modules
from messages.basic import UAResponse, UARequest, Error  # Import Basic messages
# Import the fund_agent_if_low function
from uagents.setup import fund_agent_if_low
import os  # Import os for environment variables if any needed

INPUT_TEXT = "Stocks rallied and the British pound gained."
AI_MODEL_AGENT_ADDRESS = "agent1q2gdm20yg3krr0k5nt8kf794ftm46x2cs7xyrm2gqc9ga5lulz9xsp4l4kk"

user = Agent(
    name="finbert_user",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

fund_agent_if_low(user.wallet.address())

finbert_user = Protocol("Request")


@finbert_user.on_interval(360, messages=UARequest)
async def text_classification(ctx: Context):
    ctx.logger.info(f"Asking AI model agent to classify: {INPUT_TEXT}")
    await ctx.send(AI_MODEL_AGENT_ADDRESS, UARequest(text=INPUT_TEXT))


@finbert_user.on_message(model=UAResponse)
async def handle_data(ctx: Context, sender: str, data: UAResponse):
    ctx.logger.info(f"Got response from AI model agent: {data.response}")


@finbert_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    ctx.logger.info(f"Got error from AI model agent: {error}")

user.include(finbert_user)

if __name__ == "__main__":
    finbert_user.run()
