from uagents import Agent, Context
from uagents import Model
import requests

class AgentReq(Model):
    description:str
    title:str
    image:str

    
MAILBOX_KEY = ''
DISCORD_WEBHOOK_URL = ''
Discord_agent = Agent(
    name="Gemini Agent",
    port=8001,
    seed="Gemini Agent secret phrase",
    endpoint=["http://localhost:8001/submit"],
    mailbox=f"{MAILBOX_KEY}@https://agentverse.ai",
)
 


def send_image_with_caption(caption, title, image_url):
    # Download the image from the URL
    response = requests.get(image_url)
    image_file = response.content

    # Example usage
    webhook_url = DISCORD_WEBHOOK_URL
    title = title + '\n\n' + caption
    files = {
        'file': ('image.png', image_file, 'image/png')
    }
    
    payload = {
        "content": title
    }
    
    response = requests.post(webhook_url, data=payload, files=files)

        
# Event handler for agent startup
@Discord_agent.on_event('startup')
async def address(ctx: Context):
    # Logging the agent's address
    ctx.logger.info(Discord_agent.address)


@Discord_agent.on_message(model=AgentReq)
async def handle_query_response(ctx: Context, sender: str, msg: AgentReq):
    send_image_with_caption(msg.description, msg.title, msg.image)

Discord_agent.run()