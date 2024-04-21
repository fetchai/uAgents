from datetime import datetime

from uagents import Agent, Context, Model


class Empty(Model):
    pass


class Request(Model):
    text: str


class Response(Model):
    timestamp: datetime
    text: str
    agent_address: str


agent = Agent(name="Rest API")

print(agent.address)


@agent.on_interval(period=15.0)
async def handle_interval(ctx: Context):
    print("Hello from the interval!", ctx.address)


@agent.on_rest_get("/rest/get", Response)
async def handle_get(ctx: Context):
    print('Hello from the "GET /hello" handler!', ctx.address)
    return {
        "timestamp": datetime.now(),
        "text": "Hello from the GET /hello handler!",
        "agent_address": ctx.address,
    }


@agent.on_rest_post("/rest/post", Request, Response)
async def handle_get(ctx: Context, req: Request) -> Response:
    print('Hello from the "POST /hello" handler!', ctx.address)
    return Response(
        text=f"Received: {req.text}",
        agent_address=ctx.address,
        timestamp=datetime.now(),
    )


if __name__ == "__main__":
    agent.run()
