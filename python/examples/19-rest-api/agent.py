from datetime import datetime
from typing import Any, Dict

from uagents import Agent, Context, Model


class Request(Model):
    text: str


class Response(Model):
    timestamp: datetime
    text: str
    agent_address: str


# You can also use empty models to represent empty request/response bodies
class EmptyResponse(Model):
    pass


agent = Agent(name="Rest API")


@agent.on_rest_get("/rest/get", Response)
async def handle_get(ctx: Context) -> Dict[str, Any]:
    print('Hello from the "GET" handler!', ctx.agent.address)
    return {
        "timestamp": datetime.now(),
        "text": "Hello from the GET handler!",
        "agent_address": ctx.agent.address,
    }


@agent.on_rest_post("/rest/post", Request, Response)
async def handle_post(ctx: Context, req: Request) -> Response:
    print('Hello from the "POST" handler!', ctx.agent.address)
    return Response(
        text=f"Received: {req.text}",
        agent_address=ctx.agent.address,
        timestamp=datetime.now(),
    )


if __name__ == "__main__":
    agent.run()
