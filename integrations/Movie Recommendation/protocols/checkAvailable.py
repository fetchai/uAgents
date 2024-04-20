
from uagents import Protocol , Model , Context
from typing import List
from utils.API import RAPID_API_HEADER
import requests
#  Define Protocol for movie recommendation system
streaming_availibility_protocol = Protocol("Streaming Availibility")


class AvailibilityRequest(Model):
    movie:str
    country:str

class MovieStream(Model):
    service:str
    quality:str
    link:str

class AvailibilityResponse(Model):
    streams : List[MovieStream]

# Define a handler for the Movie Recommendation system protocol
@streaming_availibility_protocol.on_message(model=AvailibilityRequest, replies=AvailibilityResponse)
async def on_movie_recommendation_request(ctx: Context, sender: str, msg: AvailibilityRequest):
    # Logging user request
    ctx.logger.info(f"Received movie streaming  request from {sender} for  {msg.movie}")

    try:
        # Generate movie recommendations based on the requested genres
        streams = get_availibility(msg)
        # ctx.logger.info(movie_recommendations.movies)
        # Send a successful response with the generated movie recommendations
        await ctx.send(sender,streams)
        
    # Handle any exceptions that occur during movie recommendation
    except Exception as exc:
        ctx.logger.error(f"Error in generating movie recommendations: {exc}")
        # Send an error response with details of the encountered error
        await ctx.send(
            destination=sender,
            message=exc
        )

# Include the Movie Recommendation protocol in your agent

# Define function to generate movie recommendations based on genres
def get_availibility(req):
    url = "https://streaming-availability.p.rapidapi.com/search/title"
    querystring = {"title":req.movie,"country":req.country,"show_type":"all","output_language":"en"}
    
    response = requests.get(url, headers=RAPID_API_HEADER, params=querystring)
    res = response.json()
    movie = res['result'][0]
    overview = movie['overview']
    if req.country in movie['streamingInfo'].keys():
        stream_info = movie['streamingInfo']['in']
        l  = []
        for s in stream_info:
            l.append(MovieStream(service=s['service'] , quality=s['quality'] , link=s['link']))
            return AvailibilityResponse(streams=l)
    
    stream_info = []
    return AvailibilityResponse(streams=stream_info)


    