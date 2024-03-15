from uagents import Model, Protocol, Agent, Context
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
import os
from .summary import summarize_transcript, answer_question, compress
from .utils import get_video_script

# First generate a secure seed phrase (e.g. https://pypi.org/project/mnemonic/)
SEED_PHRASE = "-- seed --"


# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")


# Then go to https://agentverse.ai, register your agent in the Mailroom
# and copy the agent's mailbox key
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY", None)
assert AGENT_MAILBOX_KEY is not None, "AGENT_MAILBOX_KEY environment variable is not set! Please set it to your agent's mailbox key!"


# Now your agent is ready to join the agentverse!
agent = Agent(
    name="video-agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)


# The request model
class SummaryRequest(Model):
    shortened: bool = Field(default=False, description="If true, the summary will be short! SET this to true if user is asking for short summary/article! If user doesn't say they want a short answer, set it to false. It's important if user is asking for a short answer set this to true.")
    model: str      = Field(default="gpt-4", description="The model to be used for summarization! Available models: gpt-4, gpt-3.5, claude-3. Set this to gpt-4 for best results! If the user wants fast results, set this to gpt-3.5! If they specify a model, use that (if available)!")
    video_link: str = Field(description="The link to the video to be summarized!")
    question: str   = Field(description="If the user asks for short summary, or summary set this field to empty. If the user asks to answer a question based on the video, set this field to the question!")


proto = Protocol("video-query", "0.1.0")


@proto.on_message(model=SummaryRequest, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: SummaryRequest):
    if msg.model not in ["gpt-4", "gpt-3.5", "claude-3"]:
        await ctx.send(
            sender,
            UAgentResponse(message="Invalid model! Following models are available: gpt-4, gpt-3.5, claude-3", type=UAgentResponseType.ERROR)
        )
        return

    try:
        transcript = get_video_script(msg.video_link)
    except Exception as e:
        await ctx.send(
            sender,
            UAgentResponse(message=f"No transcript found for video! Error: {e}", type=UAgentResponseType.ERROR)
        )
        return

    article = await summarize_transcript(transcript, msg.model)

    short_article = None
    if msg.shortened == True:
        short_article = await compress(article, msg.model)
    
    if len(msg.question) == 0:
        if msg.shortened == True:
            print("Sending short article")
            await ctx.send(
                sender,
                UAgentResponse(message=f"Short summary:\n{short_article}", type=UAgentResponseType.FINAL)
            )
        else:
            print("Sending full article")
            await ctx.send(
                sender,
                UAgentResponse(message=f"Article about the video: {article}", type=UAgentResponseType.FINAL)
            )
        return
    
    answer = await answer_question(article, msg.question, msg.model)
    
    response = "Answer: " + answer
    if msg.shortened == True:
        response += "\n\nShort Summary: " + short_article

    print("Sending answer")
    await ctx.send(
        sender,
        UAgentResponse(message=response, type=UAgentResponseType.FINAL)
    )

agent.include(proto, publish_manifest=True)


def run():
    agent.run()


if __name__ == "__main__":
    run()
