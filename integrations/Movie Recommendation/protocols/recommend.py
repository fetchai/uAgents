
from uagents import Protocol , Model , Context
from typing import List
from utils.data import genresData
from utils.API import TMDB_HEADER
import requests
#  Define Protocol for movie recommendation system
movie_recommendation_protocol = Protocol("Movie Recommendation System")


class RecommendationRequest(Model):
    genres: List[str]

class RecommendationResponse(Model):
    movies : List[str]


class GenresList(Model):
    genres: List[str]

class getGenre(Model):
    msg:str

@movie_recommendation_protocol.on_message(getGenre , GenresList)
async def give_genres_list(ctx:Context,sender: str, msg: RecommendationRequest):
    a = []
    for g in genresData:
        a.append(g['name'])
    await ctx.send(sender , GenresList(genres=a))

# Define a handler for the Movie Recommendation system protocol
@movie_recommendation_protocol.on_message(model=RecommendationRequest, replies=RecommendationResponse)
async def on_movie_recommendation_request(ctx: Context, sender: str, msg: RecommendationRequest):
    # Logging user request
    ctx.logger.info(f"Received movie recommendation request from {sender} with genres: {msg.genres}")

    try:
        # Generate movie recommendations based on the requested genres
        movie_recommendations = generate_movie_recommendations(msg.genres)
        # ctx.logger.info(movie_recommendations.movies)
        # Send a successful response with the generated movie recommendations
        await ctx.send(sender,movie_recommendations)
        
    # Handle any exceptions that occur during movie recommendation
    except Exception as exc:
        ctx.logger.error(f"Error in generating movie recommendations: {exc}")
        # Send an error response with details of the encountered error
        await ctx.send(
            destination=sender,
           message=movie_recommendations
        )

# Include the Movie Recommendation protocol in your agent

# Define function to generate movie recommendations based on genres
def generate_movie_recommendations(genres):
    genre_ids = []
    for genre in genres:
        genre_id = next((item["id"] for item in genresData if item["name"].lower() == genre.lower()), None)
        if genre_id:
            genre_ids.append(genre_id)
    # TMDB API key
    genre_ids_str = '%2C'.join(map(str, genre_ids))
    url = f"https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc&with_genres={genre_ids_str}"

   

    response = requests.get(url, headers=TMDB_HEADER)
    # Fetch top-rated movies based on genres from TMDB API
    
    movies_data = response.json()
    # Extract relevant information from movie data (e.g., movie titles)
    movie_recommendations = []
    for movie in movies_data['results']:
        movie_recommendations.append(movie['title'])

    return RecommendationResponse(movies=movie_recommendations)

