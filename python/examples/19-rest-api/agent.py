import time
from typing import Any, Dict

from uagents import Agent, Context, Model


class Request(Model):
    text: str


class Response(Model):
    timestamp: int
    text: str
    agent_address: str


# You can also use empty models to represent empty request/response bodies
class EmptyMessage(Model):
    pass


agent = Agent(name="Rest API")


@agent.on_rest_get("/rest/get", Response)
async def handle_get(ctx: Context) -> Dict[str, Any]:
    ctx.logger.info("Received GET request")
    return {
        "timestamp": int(time.time()),
        "text": "Hello from the GET handler!",
        "agent_address": ctx.agent.address,
    }


@agent.on_rest_post("/rest/post", Request, Response)
async def handle_post(ctx: Context, req: Request) -> Response:
    ctx.logger.info("Received POST request")
    return Response(
        text=f"Received: {req.text}",
        agent_address=ctx.agent.address,
        timestamp=int(time.time()),
    )


if __name__ == "__main__":
    agent.run()
