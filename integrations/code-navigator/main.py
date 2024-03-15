import os

from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Model, Protocol

from chain import get_lines

SEED_PHRASE = os.environ.get("SEED_PHRASE", "code navigator seed phrase")
ENDPOINT = os.environ.get("ENDPOINT", "http://localhost:8000/submit")
PORT = 8000


class CodeLinesRequest(Model):
    repository: str
    prompt: str


agent = Agent(name="code-navigator", seed=SEED_PHRASE, port=PORT, endpoint=ENDPOINT)


protocol = Protocol(name="Code Navigator")


@protocol.on_message(CodeLinesRequest, replies=UAgentResponse)
async def get_code_lines(ctx: Context, sender: str, msg: CodeLinesRequest):
    lines = get_lines(msg.repository, msg.prompt)
    await ctx.send(
        sender,
        UAgentResponse(
            type=UAgentResponseType.FINAL,
            message=f"Here is the relevant code: {lines}",
        ),
    )


agent.include(protocol, publish_manifest=True)


if __name__ == "__main__":
    agent.run()
