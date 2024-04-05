# Import necessary libraries
import requests
from ai_engine import UAgentResponse, UAgentResponseType

# Define the model for movie search
class MovieSearch(Model):
    movie_name: str

# Define the function to search for movie details
def search_movie(movie_name):
    # RapidAPI key
    rapidapi_key = 'e3a26d3d91msh1df956f0cff2a43p1c4efbjsn35d8a93e0c81'
    # Endpoint URL
    url = "https://movie-tv-music-search-and-download.p.rapidapi.com/search"
    # Query parameters
    querystring = {"keywords": movie_name, "quantity": "5", "page": "1"}
    # Headers
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "movie-tv-music-search-and-download.p.rapidapi.com"
    }
    # Send request to the API
    response = requests.get(url, headers=headers, params=querystring)
    # Parse the response JSON
    data = response.json()
    # Extract relevant information from the response
    results = []
    if 'result' in data:
        for item in data['result']:
            result = {
                'title': item.get('title', 'N/A'),
                'size': item.get('size', 'N/A'),
                'torrent': item.get('torrent', 'N/A')
            }
            results.append(result)
    return results

# Define the protocol for movie search
movie_search_protocol = Protocol("Movie Search")

# Define a handler for the Movie Search protocol
@movie_search_protocol.on_message(model=MovieSearch, replies=UAgentResponse)
async def on_movie_search_request(ctx: Context, sender: str, msg: MovieSearch):
    ctx.logger.info(f"Received movie search request from {sender} for movie: {msg.movie_name}")
    try:
        # Perform movie search
        results = search_movie(msg.movie_name)
        # Format the response
        if results:
            message = "Here are some search results:\n"
            for result in results:
                message += f"Title: {result['title']}\nSize: {result['size']}\nTorrent: {result['torrent']}\n\n"
        else:
            message = "No results found for the given movie name."
        # Send the response
        await ctx.send(sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL))
    except Exception as exc:
        ctx.logger.error(f"Error in movie search: {exc}")
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Error in movie search: {exc}",
                type=UAgentResponseType.ERROR
            )
        )

# Include the Movie Search protocol in your agent
agent.include(movie_search_protocol)
