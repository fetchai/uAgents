# Import required libraries
from ai_engine import Agent, Context, Protocol, Model, UAgentResponse, UAgentResponseType
from ai_engine.utils import http

# Extend your protocol with Podcast search request
class PodcastSearchRequest(Model):
    query: str = "star wars"

# Function to make ListenNotes API request
async def test_listennotes_api_request(ctx: Context, sender: str, msg: PodcastSearchRequest):
    url = "https://listennotes.p.rapidapi.com/api/v1/search"
    querystring = {
        "q": msg.query,
        "type": "episode",
        "genre_ids": "68,82",
        "language": "English",
        "safe_mode": "1",
        "sort_by_date": "0",
        "offset": "0",
        "only_in": "title",
        "len_max": "10",
        "len_min": "2",
        "published_after": "1390190241000",
        "published_before": "1490190241000"
    }
    
    headers = {
        "X-RapidAPI-Key": "api-key",
        "X-RapidAPI-Host": "listennotes.p.rapidapi.com"
    }

    response = await http.get(url, headers=headers, params=querystring)
    return UAgentResponse(message=response.json(), type=UAgentResponseType.FINAL)

# Test class for Fetch.ai AI Agent tech
class TestListenNotesAPI(object):
    async def test_listennotes_api_request(self, ctx: Context, sender: str):
        msg = PodcastSearchRequest(query="star wars")
        response = await test_listennotes_api_request(ctx, sender, msg)
        assert 'results' in response.message

# Now your agent is ready to join the agentverse!
agent = Agent(name="Podcast Search Agent")

protocol = Protocol("Podcast Search Protocol")

@protocol.on_message(model=PodcastSearchRequest, replies={UAgentResponse})
async def search_podcasts(ctx: Context, sender: str, msg: PodcastSearchRequest):
    response = await test_listennotes_api_request(ctx, sender, msg)
    await ctx.send(sender, response)

agent.include(protocol, publish_manifest=True)
agent.run()
