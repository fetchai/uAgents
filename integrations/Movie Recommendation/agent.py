# Import required libraries
from uagents import Agent, Bureau , Context  , Model
from protocols.recommend import movie_recommendation_protocol , RecommendationRequest , RecommendationResponse , getGenre , GenresList
from protocols.checkAvailable import AvailibilityRequest , AvailibilityResponse , streaming_availibility_protocol
# Define the Model for movie recommendation

Tom = Agent(
    name="Tom",
    seed="Avrakadavra",
)

user= Agent(
    name="sufi",
    seed="PICT"
)

class Confirm(Model):
    msg:str



Tom.include(movie_recommendation_protocol)
Tom.include(streaming_availibility_protocol)



@user.on_event("startup")
async def start(ctx:Context):
    req = getGenre(msg="Suggest me a good movie to watch tonight!")
    ctx.logger.info("Suggest me a good movie to watch tonight!")
    await ctx.send(Tom.address , req)

@user.on_message(GenresList , RecommendationRequest)
async def say_hello(ctx: Context , sender : str , msg:GenresList):
    menu = "\n"
    for i , m  in enumerate(msg.genres):
        menu += f"{i}. {m}.\n"
    ctx.logger.info(menu)
    genre = input("Enter Your Favourite Genres space separated :")
    selection = [msg.genres[int(i)] for i in genre.split(' ')]
    request = RecommendationRequest(genres=selection)
    await ctx.send(sender , message=request)


@user.on_message(RecommendationResponse , AvailibilityRequest )
async def handle_response(ctx : Context , sender :str , msg : RecommendationResponse):
    menu = "\n"
    for i , m  in enumerate(msg.movies):
        menu += f"{i}. {m}.\n"
    ctx.logger.info(menu)
    opt = int(input("Enter Index of Movie to see Where to Watch: "))

    movie = msg.movies[opt]
    country = 'in'
    req = AvailibilityRequest(movie=movie , country=country)
    await ctx.send(sender , req)



@user.on_message(AvailibilityResponse , Confirm )
async def handle_response(ctx : Context , sender :str , msg : AvailibilityResponse):
    if len(msg.streams) > 0:
        streams = msg.streams
        ctx.logger.info('Movie Available at')
        menu = '\n'
        for i, s in enumerate(streams):
            menu += f"{i}. Platform:{s.service}\nLink:{s.link}\n"
    
        ctx.logger.info(menu)
        
    else:
        ctx.logger.info('Sorry could not find Movie, may  not be Available On OTT till now')
    ctx.logger.info("DONE")
    



bureau = Bureau()
bureau.add(Tom)
bureau.add(user)

if __name__ == "__main__":
    bureau.run()

