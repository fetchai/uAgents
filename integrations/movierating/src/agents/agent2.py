# agent2  
import requests
from uagents import Agent, Context, Model

# To receive messages to your Fetch.ai wallet (set to the Dorado testnet), enter your wallet address below:
MY_WALLET_ADDRESS = "fetch1___"

from user import movie_id

movie_id= str(movie_id)

# Movie Database API URL and headers
MOVIES_API_URL = f"https://moviesdatabase.p.rapidapi.com/titles/{movie_id}/ratings"
headers = {
    'x-rapidapi-key': "ca01df7077mshfea6d79a8320efdp10da96jsn10b31a2749f8",
    'x-rapidapi-host': "moviesdatabase.p.rapidapi.com"
}

# Threshold rating for movie alerts
THRESHOLD_RATING = 2.0

# Function to fetch the top rated movie
def get_top_rated_movie():
    response = requests.get(MOVIES_API_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            top_movie = data['results']
            return top_movie
    else:
        return None

# Initialize the agent
agent2 = Agent(name="agent2")
# Function to handle movie alerts based on threshold rating
@agent2.on_interval(period=2.0)
async def handle_movie_alert(ctx: Context):
    movie = get_top_rated_movie()

    if movie:
        # ctx.logger.info(movie) --->to check data stored in movie.
        movie_rating = movie['averageRating']
        movie_votes = movie['numVotes']
        ctx.logger.info(f"The movie has rating of {movie_rating} with {movie_votes} votes")

        # Send alert to wallet address
        if MY_WALLET_ADDRESS != "fetch1___":
            await ctx.send_wallet_message(MY_WALLET_ADDRESS, alert)
        else:
            ctx.logger.info("To receive wallet alerts, set 'MY_WALLET_ADDRESS' to your wallet address.")
    else:
        ctx.logger.info("Failed to retrieve the top rated movie")

#Run the agent
agent2.run()