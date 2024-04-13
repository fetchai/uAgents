import requests
from uagents import Agent, Context, Protocol, Model
from ai_engine import UAgentResponse, UAgentResponseType

# Define a model class for the Random Meme Request agent's expected message format.
class RandomMemeRequest(Model):
    pass

# Define a function to fetch a random meme from the API.
async def fetch_random_meme():
    url = "https://meme-api.com/gimme"
    response = requests.get(url)
    meme_data = response.json()
    meme_url = meme_data.get('url')
    return meme_url


# Create a protocol for the Random Meme Request agent, specifying its communication protocol.
random_meme_protocol = Protocol(name='Random Meme protocol')

# Define a handler for the Random Meme Request protocol.
@random_meme_protocol.on_message(model=RandomMemeRequest, replies=UAgentResponse)
async def handle_random_meme_message(ctx: Context, sender: str, msg: RandomMemeRequest):
    # Call fetch_random_meme function to get a random meme.
    meme_url = await fetch_random_meme()

    # Send the meme URL to the user.
    message = f'<a href="{meme_url}">Click here for the meme!</a>'

    # Send the formatted message to the user.
    await ctx.send(sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL, html=True))
# Include the Random Meme protocol in your agent.
agent.include(random_meme_protocol, publish_manifest=True)