import os
import requests
from uagents import Agent, Context, Protocol
from messages import UAResponse, UARequest, Error
from uagents.setup import fund_agent_if_low

# Define constants
HUGGING_FACE_ACCESS_TOKEN = os.getenv("HUGGING_FACE_ACCESS_TOKEN", "")

if not HUGGING_FACE_ACCESS_TOKEN:
    raise Exception(
        "You need to provide an HUGGING_FACE_ACCESS_TOKEN, by exporting env, please follow the README"
    )

BERT_BASE_URL = "https://api-inference.huggingface.co/models/bert-base-cased"

# Set headers for API requests
HEADERS = {"Authorization": f"Bearer {HUGGING_FACE_ACCESS_TOKEN}"}


def create_and_fund_agent() -> Agent:
    """
    Create an agent for BERT-based text prediction and fund it if necessary.

    Returns:
        Agent: The created and funded agent.
    """
    agent = Agent(
        name="bert_base_agent",
        seed=HUGGING_FACE_ACCESS_TOKEN,
    )
    os.environ["AI_MODEL_AGENT_ADDRESS"] = agent.address
    fund_agent_if_low(agent.wallet.address())
    return agent


agent = create_and_fund_agent()
# Define a protocol for UARequests
bert_prediction_protocol = Protocol("UARequest")


async def predict_text(ctx: Context, sender: str, text: str) -> None:
    """
    Predict text using the Hugging Face BERT-based model and send the result as a response.

    Args:
        ctx (Context): The context object.
        sender (str): The sender's identifier.
        text (str): The text to be classified.
    """
    try:
        response = requests.post(BERT_BASE_URL, headers=HEADERS, json={"inputs": text})

        if response.status_code != 200:
            error_message = response.json().get("error", "Unknown error")
            await ctx.send(sender, Error(error=f"API Error: {error_message}"))
            return

        model_result = response.json()[0]
        await ctx.send(sender, UAResponse(response=model_result))
    except Exception as ex:
        await ctx.send(sender, Error(error=f"Exception: {str(ex)}"))


@bert_prediction_protocol.on_message(model=UARequest, replies={UAResponse, Error})
async def handle_request(ctx: Context, sender: str, request: UARequest) -> None:
    """
    Handle UARequest for text prediction and send the response.

    Args:
        ctx (Context): The context object.
        sender (str): The sender's identifier.
        request (UARequest): The UARequest containing the text to classify.
    """
    ctx.logger.info(f"Got request from {sender} for text prediction: {request.text}")
    await predict_text(ctx, sender, request.text)


agent.include(bert_prediction_protocol)

if __name__ == "__main__":
    bert_prediction_protocol.run()
