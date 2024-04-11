import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Model, Context, Protocol
from uagents.setup import fund_agent_if_low
from messages_helper.helper import Random_search, Random_result



word_give_protocol = Protocol("word_give_protocol")

word_give_agent = Agent(
    name='word_give_agent',
    port = 1124,
    seed = 'wg agent secret seed phrase',
    endpoint = 'http://localhost:1124/submit'
)

fund_agent_if_low(word_give_agent.wallet.address())

def random_search():
    url = "https://wordsapiv1.p.rapidapi.com/words/"
    querystring = {"random": "true"}
    headers = {
        "X-RapidAPI-Key": "ea14030d32msha888fd2d309cf5bp1c98c6jsnde5748e469da",
        "X-RapidAPI-Host": "wordsapiv1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    if "word" in data:
        word = data["word"]
        results = data.get("results", [])
        
        formatted_response = {
            "word": word,
            "results": results
        }
        
        return formatted_response
    else:
        return None
    
@word_give_agent.on_event('startup')
async def agent_address(ctx: Context):
    ctx.logger.info(word_give_agent.address)
    
@word_give_agent.on_message(model=Random_search)
async def give_random_word(ctx: Context, sender:str, message: Random_result):
    word_details = random_search()
    results = word_details["results"] if "results" in word_details else []
    syllables = word_details["syllables"] if "syllables" in word_details else {"blank" : "find on own :)"}
    pronunciation = word_details["pronunciation"] if "pronunciation" in word_details else {"blank" : "find on own :)"}
    if word_details:
        await ctx.send(sender, Random_result(word=word_details["word"], results=results, syllables=syllables, pronunciation=pronunciation))
    else:
        ctx.logger.info("Word not found")


if __name__ == "__main__":
    word_give_agent.run()