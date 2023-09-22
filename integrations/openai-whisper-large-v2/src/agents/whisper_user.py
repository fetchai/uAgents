from uagents import Agent, Context, Protocol
from messages.whisper_basic import AudioTranscriptRequest, AudioTranscriptResponse, Error
from uagents.setup import fund_agent_if_low
import base64
import os

RECORDING_FILE = "sample-recording/sample.flac"

WHISPER_AGENT_ADDRESS = os.getenv(
    "WHISPER_AGENT_ADDRESS", "WHISPER_AGENT_ADDRESS")

if WHISPER_AGENT_ADDRESS == "WHISPER_AGENT_ADDRESS":
    raise Exception(
        "You need to provide an WHISPER_AGENT_ADDRESS, by exporting env. Follow README for more details")

# Define user agent with specified parameters
user = Agent(
    name="whisper_user",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

# Check and top up the agent's fund if low
fund_agent_if_low(user.wallet.address())


@user.on_event("startup")
async def initialize_storage(ctx: Context):
    ctx.storage.set("AudioTranscriptSuccessful", False)


# Create an instance of Protocol with a label "WhisperModelUser"
whisper_user = Protocol(name="WhisperModelUser", version="0.1.0")


# This is an asynchronous function that is set to run at intervals of 30 sec.
# It opens the specified RECORDING_FILE, reads it and encodes in base64 format.
# Afterwards, it sends a request with the encoded data to the AI uagent's address.
@whisper_user.on_interval(period=30, messages=AudioTranscriptRequest)
async def transcript(ctx: Context):
    AudioTranscriptSuccessful = ctx.storage.get("AudioTranscriptSuccessful")

    if not AudioTranscriptSuccessful:
        # Opening the file in read binary mode
        with open(RECORDING_FILE, "rb") as f:
            # Encoding the audio data to base64
            data = base64.b64encode(f.read()).decode('ascii')
        # Using the context to send the request to the desired address with the audio data
        await ctx.send(WHISPER_AGENT_ADDRESS, AudioTranscriptRequest(audio_data=data))


@whisper_user.on_message(model=AudioTranscriptResponse)
async def handle_data(ctx: Context, sender: str, audioTranscript: AudioTranscriptResponse):
    ctx.logger.info(f"audio transcript => {audioTranscript.transcript}")
    ctx.storage.set("AudioTranscriptSuccessful", True)


@whisper_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    ctx.logger.info(f"Got error from uagent: {error}")

# Include the protocol with the agent, publish_manifest will make the protocol details available on Agentverse.
user.include(whisper_user, publish_manifest=True)

# Initiate the audio AudioTranscripting task
if __name__ == "__main__":
    whisper_user.run()
