import time
import random
import requests
import os
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model

class JokeRequest(Model):
    category: str = "Any"
def fetch_joke(category="Any"):
        url = f"https://v2.jokeapi.dev/joke/Any?blacklistFlags=political,explicit&format=json"
        response = requests.get(url)
        joke_data = response.json()
        return joke_data

def post_joke(joke_data):
        if joke_data["type"] == "single":
            print(joke_data["joke"])
        else:
            print(joke_data["setup"])
            print(joke_data["delivery"])

def run():
            joke_request = JokeRequest()  # Create a new joke request
            joke_data = self.fetch_joke(joke_request.category)
            post_joke(joke_data)
eth_protocol = Protocol("JokeAPI Protocol")

@eth_protocol.on_message(model=JokeRequest, replies={UAgentResponse})
async def Tell_Joke(ctx: Context, sender: str, msg: JokeRequest):
    joke_data = fetch_joke(msg.category)
    content = ""
    if joke_data["type"] == "single":
        content += f"{joke_data['joke']}"
    else:
        content += f"{joke_data['setup']}\n\n\n\n"
        content += f"{joke_data['delivery']}"
    await ctx.send(sender, UAgentResponse(message=content, type=UAgentResponseType.FINAL))
agent.include(eth_protocol,publish_manifest=True)
