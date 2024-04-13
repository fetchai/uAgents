import requests
from uagents import Agent, Context, Model,Protocol
from ai_engine import UAgentResponse, UAgentResponseType
from message import Movie
# To receive messages to your Fetch.ai wallet (set to the Dorado testnet), enter your wallet address below:
MY_WALLET_ADDRESS = "fetch1___"

from user import get_movie_id




# Movie Database API URL and headers

headers = {
    'x-rapidapi-key': "ca01df7077mshfea6d79a8320efdp10da96jsn10b31a2749f8",
    'x-rapidapi-host': "moviesdatabase.p.rapidapi.com"
}


# Function to fetch the top rated movie
def get_top_rated_movie(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            top_movie = data['results']
            return top_movie
    else:
        return None

# Initialize the agent

proto = Protocol("movie")


@proto.on_message(model = Movie, replies={UAgentResponse})
async def get_movie_data(ctx: Context, sender: str, msg: Movie):
    ctx.logger.info(f"{msg}")
    movie_id = await get_movie_id(msg.title)
    
    MOVIES_API_URL = f"https://moviesdatabase.p.rapidapi.com/titles/{movie_id}/ratings"
    if movie_id:
        ctx.logger.info(f"The ID of the movie '{msg.title}' is: {movie_id}")
    else:
        ctx.logger.info("Movie not found or error occurred.")
    
    movie = get_top_rated_movie(MOVIES_API_URL)

    if movie:
        # ctx.logger.info(movie) --->to check data stored in movie.
        movie_rating = movie['averageRating']
        movie_votes = movie['numVotes']
        ctx.logger.info(f"The movie has rating of {movie_rating} with {movie_votes} votes")
        msg = f"The movie has rating of {movie_rating} with {movie_votes} votes"

        # Send alert to wallet address
        if MY_WALLET_ADDRESS != "fetch1___":
            await ctx.send_wallet_message(MY_WALLET_ADDRESS, alert)
        else:
            ctx.logger.info("To receive wallet alerts, set 'MY_WALLET_ADDRESS' to your wallet address.")
    else:
        ctx.logger.info("Failed to retrieve the top rated movie")
    ctx.logger.info(msg)
    await ctx.send(
        sender, UAgentResponse(message=msg, type=UAgentResponseType.FINAL)
)


agent.include(proto,publish_manifest=True)
#Run the agent
agent.run()
