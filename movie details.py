from ai_engine import UAgentResponse, UAgentResponseType


class Movie(Model):
    down_url: str
    details: str

movie_protocol = Protocol("Movie")


@movie_protocol.on_message(model=Movie, replies={UAgentResponse})
async def roll_dice(ctx: Context, sender: str, msg: Movie):

    await ctx.send(
        sender, UAgentResponse(message=f'Details : {msg.details} Download URL: {msg.down_url}', type=UAgentResponseType.FINAL)
)

agent.include(movie_protocol, publish_manifest=True)
