import os

from ai_engine import UAgentResponse, UAgentResponseType
from dotenv import load_dotenv
from uagents import Agent, Context, Field, Model, Protocol
from uagents.setup import fund_agent_if_low
from utils import perform_speaker_diarization

load_dotenv()

AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")
HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")

agent = Agent(
    name="speaker diarization",
    seed="speaker diarization phrase",
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

protocol = Protocol("speaker diarization versions", version="0.1.1")

fund_agent_if_low(agent.wallet.address())

print(agent.address, "agent_address")


class SpeakerDiarizationInput(Model):
    url: str = Field(
        description="Describes the field where user provide the audio file url and it should be in .wav format"
    )


@protocol.on_message(model=SpeakerDiarizationInput, replies={UAgentResponse})
async def message_handler(ctx: Context, sender: str, msg: SpeakerDiarizationInput):
    ctx.logger.info(f"Received webiste {sender} url: {msg.url}.")
    try:
        result = perform_speaker_diarization(HUGGING_FACE_TOKEN, msg.url)
        final_output=""
        for i in result:
            final_output += f"Speaker : {i['speaker']} ; duration : {i['end']-i['start']} \n"
        await ctx.send(
            sender, UAgentResponse(message=final_output, type=UAgentResponseType.FINAL)
        )
    except Exception as e:
        ctx.logger.error(f"Somethig went wrong while diarization. {e}")
        result = "Somethig went wrong while diarization."
        await ctx.send(
            sender, UAgentResponse(message=result, type=UAgentResponseType.ERROR)
        )


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
