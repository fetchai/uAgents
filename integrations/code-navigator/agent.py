import os

from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Model, Protocol

from chain import get_code_snippets

SEED_PHRASE = os.environ.get("SEED_PHRASE", "code navigator mailbox seed phrase")
ENDPOINT = os.environ.get("ENDPOINT", "http://localhost:8000/submit")
MAILBOX_KEY = os.environ.get("MAILBOX_KEY", "1153406c-7575-4c54-a7d6-7f2a2c8c0b50")
PORT = 8000


class CodeLinesRequest(Model):
    repository: str
    prompt: str


agent = Agent(name="code-navigator", seed=SEED_PHRASE, port=PORT, mailbox=MAILBOX_KEY)


protocol = Protocol(name="Code Navigator")


@protocol.on_message(CodeLinesRequest, replies=UAgentResponse)
async def get_code_lines(ctx: Context, sender: str, msg: CodeLinesRequest):
    lines = get_code_snippets(msg.repository, msg.prompt)
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
