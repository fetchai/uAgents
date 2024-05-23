import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Model, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents import Model
from messages_helper.helper import *


word_search_agent = Agent(
    name = 'word_search_agent',
    port = 1123,
    seed = 'ws agent secret seed phrase',
    endpoint = 'http://localhost:1123/submit'
)

fund_agent_if_low(word_search_agent.wallet.address())


word_search_protocol = Protocol("ws Protocol")

def get_word_details(word):
    url = f"https://wordsapiv1.p.rapidapi.com/words/{word}"

    headers = {
        "X-RapidAPI-Key": "ea14030d32msha888fd2d309cf5bp1c98c6jsnde5748e469da",
        "X-RapidAPI-Host": "wordsapiv1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if "word" in data:
        word = data["word"]
        results = data.get("results", [])
        syllables = data.get("syllables", {})
        pronunciation = data.get("pronunciation", {})
        
        formatted_response = {
            "word": word,
            "results": results,
            "syllables": syllables,
            "pronunciation": pronunciation
        }
        
        return formatted_response
    else:
        return None
    
@word_search_agent.on_event('startup')
async def agent_address(ctx: Context):
    ctx.logger.info(word_search_agent.address)    

@word_search_agent.on_message(model=Given_word)
async def reply(ctx: Context, sender:str,message: Result):
    word = message.word
    word_details = get_word_details(word)
    syllables = {}
    pronunciation = {}
    if word_details:
       await ctx.send(sender, Result(word=word_details["word"], result=word_details["results"], syllables=word_details["syllables"], pronunciation=word_details["pronunciation"]))
    else:
        ctx.logger.info("Word not found")
        

        
if __name__ == "__main__":
    word_search_agent.run()