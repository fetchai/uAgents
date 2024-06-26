from uagents import Agent, Context, Model


class AIRequest(Model):
    prompt: str


agent = Agent(
    name="ai_agent",
    seed="987wefqw23r2365432100weffwewfw000fwe00000",
    port=8001,
    endpoint="http://127.0.0.1:8001/submit",
    log_level="DEBUG",
)


class AIResponse(Model):
    response: str


@agent.on_message(model=AIRequest, replies=AIResponse)
async def respond_to_adapter(ctx: Context, sender: str, msg: AIRequest):
    ctx.logger.info(f"Message from AI Adapter: {msg.prompt}")

    # TODO: implement AI Agent logic here

    # TODO: send back the actual AI response to the Adapter agent
    await ctx.send(sender, AIResponse(response="AI response"))
