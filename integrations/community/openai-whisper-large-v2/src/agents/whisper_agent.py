from uagents import Agent, Context, Protocol
from messages.whisper_basic import AudioTranscriptRequest, AudioTranscriptResponse, Error
from uagents.setup import fund_agent_if_low
import os
import requests
import base64

# Get the HUGGING_FACE_ACCESS_TOKEN from environment variable or default to a placeholder string if not found.
HUGGING_FACE_ACCESS_TOKEN = os.getenv(
    "HUGGING_FACE_ACCESS_TOKEN", "HUGGING_FACE_ACCESS_TOKEN")

if HUGGING_FACE_ACCESS_TOKEN == "HUGGING_FACE_ACCESS_TOKEN":
    raise Exception(
        "You need to provide an HUGGING_FACE_ACCESS_TOKEN, by exporting env. Follow README for more details")

WHISPER_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v2"

# Define headers for HTTP request, including content type and authorization details
HEADERS = {
    "Authorization": f"Bearer {HUGGING_FACE_ACCESS_TOKEN}"
}

# Create an agent with predefined properties
agent = Agent(
    name="whisper_agent",
    seed=HUGGING_FACE_ACCESS_TOKEN,
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

# Ensure the agent has enough funds
fund_agent_if_low(agent.wallet.address())


async def get_audio_transcript(ctx: Context, sender: str, audiodata: str):
    try:
        # Encoding the audio data from ASCII to bytes
        audiodata = audiodata.encode("ascii")
        # Converting the audio data from base64 to bytes
        audioBytes = base64.b64decode(audiodata)

        # Sending POST request to WHISPER_URL with audio bytes
        response = requests.post(WHISPER_URL, headers=HEADERS, data=audioBytes)

        # If the request response is not successful (non-200 code), send error message
        if response.status_code != 200:
            await ctx.send(sender, Error(error=f"Error: {response.json().get('error')}"))
            return

        # Send the parsed response back to the sender/user
        await ctx.send(sender, AudioTranscriptResponse(transcript=response.json().get('text')))
        return

    # If an unknown exception occurs, send a generic error message to the sender/user
    except Exception as ex:
        await ctx.send(sender, Error(error=f"Exception detail: {ex}"))
        return

# Create an instance of Protocol with a label "WhisperModelAgent"
whisper_agent = Protocol(name="WhisperModelAgent", version="0.1.0")


@whisper_agent.on_message(model=AudioTranscriptRequest, replies={AudioTranscriptResponse, Error})
async def handle_request(ctx: Context, sender: str, request: AudioTranscriptRequest):
    # Log the request details
    ctx.logger.info(f"Got request from  {sender}")

    await get_audio_transcript(ctx, sender, request.audio_data)


# Include the protocol with the agent, publish_manifest will make the protocol details available on Agentverse.
agent.include(whisper_agent, publish_manifest=True)

# Define the main entry point of the application
if __name__ == "__main__":
    whisper_agent.run()
