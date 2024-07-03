from dotenv import load_dotenv
load_dotenv()

from crewai import Crew
from crewagents import Agents
from tasks import Tasks
import pydantic
from uagents import Agent, Protocol, Context, Model
from uagents.setup import fund_agent_if_low

class YoutubeQuery(Model):
    youtube_video_url : str
    search_query : str

class YoutubeResponse(Model):
    result: str

agent = Agent(
    name = 'Youtube Query Agent',
    seed = '<Replace with your seed phrase>',
    port = 8000,
    endpoint = ['http://localhost:8000/submit']
)

fund_agent_if_low(agent.wallet.address())

@agent.on_event('startup')
async def agent_details(ctx: Context):
    ctx.logger.info(f'My agent address is: {agent.address}')


async def crew_ai(youtube_video_url, search_query):
    agents = Agents()
    tasks = Tasks()

    youtube_search_agent = agents.youtube_search_agent(youtube_video_url)
    research_youtube_content_task = tasks.research_youtube_content_task(youtube_search_agent, search_query, youtube_video_url)

    # Instantiate the crew with a single agent and task
    crew = Crew(
        agents=[youtube_search_agent],
        tasks=[research_youtube_content_task]
    )

    # Kick off the process
    result = crew.kickoff()
    return result

youtube_protocol = Protocol('Youtube Protocol')

@youtube_protocol.on_message(model =YoutubeQuery, replies = {YoutubeResponse})
async def youtube_query(ctx: Context, sender: str, msg: YoutubeQuery):
    ctx.logger.info(f'User youtube url {msg.youtube_video_url} and query is {msg.search_query}')
    result = await crew_ai(msg.youtube_video_url, msg.search_query)
    ctx.logger.info(result)
    await ctx.send(sender, YoutubeResponse(result = str(result)))

agent.include(youtube_protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()