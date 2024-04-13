import requests
from uagents import Agent, Context, Model

# To receive messages to your Fetch.ai wallet (set to the Dorado testnet), enter your wallet address below:
MY_WALLET_ADDRESS = "fetch1___"

from user import movie_id

movie_id= str(movie_id)

# Movie Database API URL and headers
MOVIES_API_URL1 = f"https://moviesdatabase.p.rapidapi.com/titles/{movie_id}"


headers1 = {
    'x-rapidapi-key': "ca01df7077mshfea6d79a8320efdp10da96jsn10b31a2749f8",
    'x-rapidapi-host': "moviesdatabase.p.rapidapi.com"
}

def get_movie_name():
    response = requests.get(MOVIES_API_URL1, headers=headers1)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            movie_info = data['results']  # Select the first result
            # Extracting movie title and year
            movie_title = movie_info['titleText']['text']
            movie_year = movie_info['releaseYear']['year']
            return movie_title, movie_year
    return None, None

# Initialize the agent
agent1 = Agent(name="agent1")

# Function to handle movie alerts based on threshold rating
@agent1.on_interval(period=5)
async def handle_movie_alert(ctx: Context):
    movie_title, movie_year = get_movie_name()

    if movie_title and movie_year:
        ctx.logger.info(f"The movie is {movie_title} released in {movie_year}")
    else:
        ctx.logger.info("Failed to retrieve movie information.")

agent1.run()
