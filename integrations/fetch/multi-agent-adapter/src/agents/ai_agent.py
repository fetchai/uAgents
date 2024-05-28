class AIRequest(Model):
    prompt: str


class AIResponse(Model):
    response: str


@agent.on_message(model=AIRequest, replies=AIResponse)
async def respond_to_adapter(ctx: Context, sender: str, msg: AIRequest):
    ctx.logger.info(f"Message from AI Adapter: {msg.prompt}")

    # TODO: implement AI Agent logic here

    # TODO: send back the actual AI response to the Adapter agent
    await ctx.send(sender, AIResponse(response="AI response"))
