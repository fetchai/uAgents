# Import required libraries
import requests
import spotipy
import os
from spotipy.oauth2 import SpotifyClientCredentials
from uagents import Agent, Model, Context, Protocol
from ai_engine import UAgentResponse, UAgentResponseType
from uagents.setup import fund_agent_if_low
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define Request Data Model
class SongRequest(Model):
    keyword: str

# Agent Configuration
AGENT_MAILBOX_KEY = "<your_agent_mailbox_key>"
SEED_PHRASE = "<your_agent_secret_phrase>"
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

# Initialize Spotify client credentials
spotify_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
spotify_client = spotipy.Spotify(client_credentials_manager=spotify_credentials_manager)

# Define the agent
agent = Agent(
    name="spotify",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

fund_agent_if_low(agent.wallet.address())

print(agent.address)

# Define the song search function
async def search_song(keyword):
    results = spotify_client.search(q=keyword, type='track', limit=5)
    tracks = results['tracks']['items']
    return tracks

# Define the protocol
song_search_protocol = Protocol('Song Search Protocol')

@song_search_protocol.on_message(model=SongRequest, replies={UAgentResponse})
async def handle_song_request(ctx: Context, sender: str, msg: SongRequest):
    ctx.logger.info(f'User has requested to search songs for the keyword: {msg.keyword}')
    songs = await search_song(msg.keyword)
    print(songs)
    if songs:
        response_message = ""
        for idx, song in enumerate(songs):
            preview_url = song['preview_url']
            spotify_url = song['external_urls']['spotify']
            song_info = (
                f"{idx + 1}. {song['name']} by {', '.join([artist['name'] for artist in song['artists']])}<br>"
                f"   Album: {song['album']['name']}<br>"
                f"   Preview URL: {'<a href=' + preview_url + '>Preview</a>' if preview_url else 'None'}<br>"
                f"   Spotify URL: <a href='{spotify_url}'>Listen on Spotify</a><br><br>\n"
            )
            response_message += song_info
        await ctx.send(sender, UAgentResponse(message=response_message, type=UAgentResponseType.FINAL))
    else:
        await ctx.send(sender, UAgentResponse(message="No songs found.", type=UAgentResponseType.FINAL))

agent.include(song_search_protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
