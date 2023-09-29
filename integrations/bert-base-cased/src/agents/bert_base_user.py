import os
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low

from messages import Error, UARequest, UAResponse

# Constants
INPUT_TEXT = "India is a [MASK] Capital of World."
AI_MODEL_AGENT_ADDRESS = os.getenv("AI_MODEL_AGENT_ADDRESS", "")

# Create a user agent
user = Agent(
    name="bert_base_user",
)

# Fund the user agent if necessary
fund_agent_if_low(user.wallet.address())

# Define a protocol for user-agent communication
bert_base_user = Protocol("Request")

@bert_base_user.on_interval(360, messages=UARequest)
async def predict_masking(ctx: Context):
    """
    Periodically sends a UARequest to the AI model agent to predict a masking word.

    Args:
        ctx (Context): The context object.
    """
    ctx.logger.info(f"Asking AI model agent to find masking word: {INPUT_TEXT}")
    await ctx.send(AI_MODEL_AGENT_ADDRESS, UARequest(text=INPUT_TEXT))

@bert_base_user.on_message(model=UAResponse)
async def handle_data(ctx: Context, sender: str, data: UAResponse):
    """
    Handles the response data received from the AI model agent.

    Args:
        ctx (Context): The context object.
        sender (str): The sender's identifier.
        data (UAResponse): The UAResponse containing the predicted masking word.
    """
    ctx.logger.info(f"Got response from AI model agent: {data.response}")

@bert_base_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    """
    Handles error messages received from the AI model agent.

    Args:
        ctx (Context): The context object.
        sender (str): The sender's identifier.
        error (Error): The Error message from the AI model agent.
    """
    ctx.logger.info(f"Got error from AI model agent: {error}")

# Include the user agent in the agent setup
user.include(bert_base_user)
