# Import Required Libraries
import openai
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
import os
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

# Define a model for the translation request, specifying the source and target languages, and the sentence to translate
class TrnRequest(Model):
    lang1: str = Field(description="What is the language from which you want to translate?")
    lang2: str = Field(description="What is the language to which you want to translate?")
    sentence: str = Field(description="What is the message you want to translate?")

# Set a unique identifier for your agent
SEED_PHRASE = "Open AI Language Translator agent"
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

# Define the unique mailbox key for the agent's communication
AGENT_MAILBOX_KEY = "8cf8952e-b972-4ebf-9f4a-dcaab29ebd42"

# Initialize the agent with its unique identifiers
translatorAgent = Agent(
    name="Open AI Language translator",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# Ensure the agent has enough funds to operate, if not, fund it
fund_agent_if_low(translatorAgent.wallet.address())

# Initialize a new protocol for the agent to handle translation requests
translator_protocol = Protocol("Translator Protocol")

# Set your OpenAI API key here
OPENAI_API_KEY = "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"

# Set the API key directly in the openai module
openai.api_key = OPENAI_API_KEY

# Define an asynchronous function to get responses from OpenAI's Chat API
async def get_chat_completion(prompt, model="gpt-3.5-turbo"):
    # Package the user's prompt into the format required by the OpenAI API
    messages = [{"role": "user", "content": prompt}]
    # Send the prompt to the OpenAI API and get the response
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.5
    )
    # Extract and return the content of the response
    return response.choices[0].message["content"]

# Define the behavior of the translator agent when it receives a translation request
@translator_protocol.on_message(model=TrnRequest, replies={UAgentResponse})
async def translate(ctx: Context, sender: str, msg: TrnRequest):
    # Use the OpenAI API to translate the requested sentence
    response = await get_chat_completion(f"Translate {msg.sentence} from {msg.lang1} to {msg.lang2}.")
    # Log the translation request details
    ctx.logger.info(f'From: {msg.lang1} \nTo: {msg.lang2} \nSentence: {msg.sentence}')
    # Send the translation back to the requester
    await ctx.send(
        sender, UAgentResponse(message=response, type=UAgentResponseType.FINAL)
    )

# Include the translation protocol in the agent's capabilities
translatorAgent.include(translator_protocol, publish_manifest=True)

# Start the agent, allowing it to begin processing requests
translatorAgent.run()
