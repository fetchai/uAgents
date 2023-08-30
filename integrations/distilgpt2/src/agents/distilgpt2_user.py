"""
This file initiates a request which is to be handled by a user. It uses the distilgpt2 model to perform a text auto-completion task.
The text to be completed is, "My name is Gaurav and ", and the completion is achieved by triggering a model agent called AI_MODEL_AGENT_ADDRESS.

The code is structured as follows:

- An agent is defined with a defined name, port, and endpoint.
- It then checks if the user agent has a low fund, if it's low, the agent's wallet will be topped up.
- An "on_interval" event handler is established to trigger an auto-complete task every 360 seconds.
- This task sends a message to the AI model agent to complete the text.
- It also contains two other event handlers - handle_data and handle_error. handle_data logs the response from the AI model agent, and handle_error handles and logs any errors that occur during the process.

Note: All communication between the user agent and AI model agent is asynchronous.
"""

from uagents import Agent, Context, Protocol  # Import necessary modules
from messages.basic import Data, Request, Error  # Import Basic messages
# Import the fund_agent_if_low function
from uagents.setup import fund_agent_if_low
import os  # Import os for environment variables if any needed

# The text to be completed by AI model
COMPLETE_THIS = "My name is Clara and I am"
# AI model agent address
AI_MODEL_AGENT_ADDRESS = "agent1q2gdm20yg3krr0k5nt8kf794ftm46x2cs7xyrm2gqc9ga5lulz9xsp4l4kk"

# Define user agent with specified parameters
user = Agent(
    name="distilgpt2_user",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

# Check and top up the agent's fund if low
fund_agent_if_low(user.wallet.address())

# Define a protocol for the user agent
distilgpt2_user = Protocol("Request")

# Define a function that sends a message to the AI model agent every 360 seconds


@distilgpt2_user.on_interval(360, messages=Request)
async def auto_complete(ctx: Context):
    ctx.logger.info(f"Asking AI model agent to complete this: {COMPLETE_THIS}")
    await ctx.send(AI_MODEL_AGENT_ADDRESS, Request(text=COMPLETE_THIS))

# Define a function to handle and log data received from the AI model agent


@distilgpt2_user.on_message(model=Data)
async def handle_data(ctx: Context, sender: str, data: Data):
    ctx.logger.info(f"Got response from AI model agent: {data.generated_text}")

# Define a function to handle and log errors occurred during text completion process


@distilgpt2_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    ctx.logger.info(f"Got error from AI model agent: {error}")

# Include the request protocol in the user definition
user.include(distilgpt2_user)

# Initiate the auto-complete task if the file is being run directly
if __name__ == "__main__":
    distilgpt2_user.run()
