import os
import requests
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents import Model
from messages_helper.helper import *

# Get the Hugging Face API token from environment variable or replace with your token
API_TOKEN = os.getenv("HUGGING_FACE_ACCESS_TOKEN", "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")

# Define the model ID for the new Hugging Face model
MODEL_ID = "google/gemma-7b"

# Define the URL for the model endpoint
MODEL_ENDPOINT = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

# Create an agent with predefined properties
agent = Agent(
    name="gemma_agent",
    seed=API_TOKEN,
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

# Ensure the agent has enough funds
fund_agent_if_low(agent.wallet.address())

# Define a function to generate response using the Hugging Face model
def generate_response(input_text):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    data = {"inputs": input_text}
    response = requests.post(MODEL_ENDPOINT, headers=headers, json=data)
    return response.json()[0]["generated_text"]  # Extract response text



# Create an instance of Protocol with a label "Request"
gemma_agent_protocol = Protocol("Request")

input_text = str(input("Enter the text to get explained: "))
@agent.on_event("startup")
async def agent_startup(ctx: Context):
    ctx.logger.info("Gemma agent started successfully")
    response = generate_response(input_text)
    ctx.logger.info(f"Response from Hugging Face model: {response}")
    prev_word = input("Do you want to use saved words: yes or no ?")
    if prev_word == "yes":
        word = ctx.storage.get("word")
        res = generate_response(word)
        ctx.logger.info(f"Response from Hugging Face model: {res}")
    else:
        ctx.logger.info("No saved word to use.")
        

# Include the protocol with the agent
agent.include(gemma_agent_protocol)


# Define the main entry point of the application
if __name__ == "__main__":
    agent.run()
