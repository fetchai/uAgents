from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
import requests

class MovieQuery(Model):
    movie_name: str = Field(description="The name of the movie to query.")

movie_query_protocol = Protocol("MovieQuery")

@movie_query_protocol.on_message(model=MovieQuery, replies={UAgentResponse})
async def query_movie(ctx: Context, sender: str, msg: MovieQuery):
    api_key = 'YOUR_API_KEY'  # Replace 'YOUR_API_KEY' with your actual API key
    url = "https://movie-database-imdb.p.rapidapi.com/movie/"
    querystring = {"name": msg.movie_name}
    headers = {
        "X-RapidAPI-Key": "e3a26d3d91msh1df956f0cff2a43p1c4efbjsn35d8a93e0c81",
        "X-RapidAPI-Host": "movie-database-imdb.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            movie_data = response.json()
            message = f"Title: {movie_data.get('name')}\n"
            message += f"Release Date: {movie_data.get('datePublished')}\n"
            message += f"Rating: {movie_data.get('rating').get('ratingValue')}\n"
            message += f"Genre: {', '.join(movie_data.get('genre'))}\n"
            message += "Actors:\n"
            for actor in movie_data.get('actor'):
                message += f"- {actor.get('name')}\n"
            message += "Director:\n"
            for director in movie_data.get('director'):
                message += f"- {director.get('name')}\n"
            message += f"Description: {movie_data.get('description')}"
        else:
            message = "Failed to fetch movie information."
    except Exception as e:
        message = f"Error: {str(e)}"
    await ctx.send(sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL))

agent.include(movie_query_protocol, publish_manifest=True)
