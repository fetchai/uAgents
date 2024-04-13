#Meant to be run online on the agentsverse platform

from uagents import Agent, Context
import json

import requests
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
 
MAILBOX_KEY = ''    #This agents Mailroom key
NEWSDATA_IO_API_KEY = ''
DISCORD_AGENT_ADDRESS = ''
BACKEND_BASE_URL = ''

agent = Agent(name="alice", mailbox=f"{MAILBOX_KEY}@https://agentverse.ai")

class Message(Model):
    message: str
    m_type:str

class AgentReq(Model):
    description:str
    title:str
    image:str

class TextToImage(Model):
    """
    Describes the input payload for converting text to an image.
    """
    text: str = Field(description="Text to convert to an image.")

description = ''

def image_gen(payload):    
    try:
        body = {
            "data": [
                payload,
                "4-Step"
            ],
            "fn_index": 0,
            "session_hash": "ad193e28-7a20-4824-8402-4a10a149a1bc"
        }
        print("First api call")
        url = 'https://bytedance-sdxl-lightning.hf.space/queue/join'
        response = requests.post(url, json=body, timeout=40)
        print(response)
        
        print("Second api call")
        url1 = 'https://bytedance-sdxl-lightning.hf.space/queue/data?session_hash=ad193e28-7a20-4824-8402-4a10a149a1bc'
        
        data_response = requests.get(url1)
        data_response_text = data_response.content.decode('utf-8')
        data_response_json = [json.loads(line.split(':', 1)[1]) for line in data_response_text.split('\n') if line.strip()]

        # Extracting URL part
        url = None
        for data in data_response_json:
            if "output" in data:
                output_data = data["output"]
                if "data" in output_data and len(output_data["data"]) > 0:
                    url = output_data["data"][0]["url"]
                    break

        print("Returning url data")
        return url
    except Exception as e:
        print(e)
        return 'ERROR generating images '

@agent.on_message(model=Message)
async def handle_query_response(ctx: Context, sender: str, msg: Message):
    if msg.m_type == 'description':
        description = msg.message
        print(description)

@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {ctx.name} and my address is {ctx.address}.")
    print('SEND IT!')



#Interaction with DeltaV

news_protocol = Protocol("News Generation")

@news_protocol.on_message(model=TextToImage, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: TextToImage):



    #FETCHING OF NEWS DATA
    url = "https://newsdata.io/api/1/news"
    params = {
        "q": "cryptocurrency",
        "apikey":  NEWSDATA_IO_API_KEY,
    }
    end_message = ''
    news_response = ''
    response = requests.get(url, params=params)

    if response.status_code == 200:
        news_data = response.json()
        articles = news_data.get("results", [])
        news_response = articles[0]

    #STORING OF NEWS DATA
    description = news_response['description']
    title = str(news_response['title'])
    news_url = news_response['url']
    end_message = end_message + title + '\n\n'

    #GENERATION OF POST DESCRIPTION
    response = requests.post(BACKEND_BASE_URL+'/api/test/', data={'prompt':description})
    description_data = json.loads(response.content)
    final_description = description_data['result']
    end_message = end_message + str(final_description) + '\n\n';

    #GENERATION OF IMAGE
    response = requests.post(BACKEND_BASE_URL+'/api/prompts/', data={'prompt':description})
    image_url = image_gen(str(response.content))
    end_message = end_message + "IMAGE : " + str(image_url);
    end_message = end_message + '\n\nFULL STORY: ' + news_url

    #POSTING OF DATA VIA OFFLINE AGENT
    await ctx.send(DISCORD_AGENT_ADDRESS, AgentReq(description = final_description, title = title, image = str(image_url)))

    #CALLBACK TO DELTAV
    await ctx.send(sender, UAgentResponse(message = end_message, type = UAgentResponseType.FINAL))
    
agent.include(news_protocol)
 
 
if __name__ == "__main__":
    agent.run()