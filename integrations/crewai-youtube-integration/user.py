from uagents import Agent, Protocol, Context, Model
from uagents.setup import fund_agent_if_low

class YoutubeQuery(Model):
    youtube_video_url : str
    search_query : str

class YoutubeResponse(Model):
    result: str

agent = Agent(
    name = 'User Agent',
    seed = '<Replace with your seed phrase>',
    port = 8001,
    endpoint = ['http://localhost:8001/submit']
)

fund_agent_if_low(agent.wallet.address())

address = '<Replace this with your crewai_agent>'

@agent.on_event('startup')
async def agent_details(ctx: Context):
    youtube_video_url = input("Provide the YouTube video URL (leave blank for general search):\n")
    search_query = input("What is the search query for the YouTube video content?\n")
    await ctx.send(address, YoutubeQuery(youtube_video_url=youtube_video_url,search_query=search_query ))
    ctx.logger.info(f'My agent address is: {agent.address}')

youtube_protocol = Protocol('Youtube Protocol')

@youtube_protocol.on_message(model =YoutubeResponse)
async def youtube_query(ctx: Context, sender: str, msg: YoutubeResponse):
    ctx.logger.info(f'Results by the user {msg.result}')
    
agent.include(youtube_protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()