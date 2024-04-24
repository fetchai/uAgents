# Necessary imports: uagents for agent creation and message handling,
# os and requests for managing API calls
from uagents import Agent, Context, Protocol
from messages.basic import UAResponse, UARequest, Error
from uagents.setup import fund_agent_if_low
import os
import requests

# The access token and URL for the FinBERT model, served by Hugging Face
HUGGING_FACE_ACCESS_TOKEN = os.getenv(
    "HUGGING_FACE_ACCESS_TOKEN", "HUGGING FACE secret phrase :)")
FINBERT_URL = "https://api-inference.huggingface.co/models/ProsusAI/finbert"

# Setting the headers for the API call
HEADERS = {
    "Authorization": f"Bearer {HUGGING_FACE_ACCESS_TOKEN}"
}

# Creating the agent and funding it if necessary
agent = Agent(
    name="finbert_agent",
    seed=HUGGING_FACE_ACCESS_TOKEN,
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)
fund_agent_if_low(agent.wallet.address())

# Function to get classification results from FinBERT for a given text


async def get_classification(ctx: Context, sender: str, text: str):
    data = {
        "inputs": text
    }

    try:
        # Making POST request to Hugging Face FinBERT API
        response = requests.post(FINBERT_URL, headers=HEADERS, json=data)

        if response.status_code != 200:
            # Error handling - send error message back to user if API call unsuccessful
            await ctx.send(sender, Error(error=f"Error: {response.json().get('error')}"))
            return
        # If API call is successful, return the response from the model
        model_res = response.json()[0]
        await ctx.send(sender, UAResponse(response=model_res))
        return
    except Exception as ex:
        # Catch and notify any exception occured during API call or data handling
        await ctx.send(sender, Error(error=f"An exception occurred while processing the request: {ex}"))
        return


# Protocol declaration for UARequests
finbert_agent = Protocol("UARequest")

# Declaration of a message event handler for handling UARequests and send respective response.


@finbert_agent.on_message(model=UARequest, replies={UAResponse, Error})
async def handle_request(ctx: Context, sender: str, request: UARequest):
    # Logging the request information
    ctx.logger.info(
        f"Got request from  {sender} for text classification : {request.text}")

    # Call text classification function for the incoming request's text
    await get_classification(ctx, sender, request.text)

# Include protocol to the agent
agent.include(finbert_agent)

# If the script is run as the main program, run our agents event loop
if __name__ == "__main__":
    finbert_agent.run()
