import os

from fastapi import FastAPI
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
)
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.utils.messages import parse_envelope, send_message_to_agent


name = "Chat Protocol Adapter"
identity = Identity.from_seed(os.environ["AGENT_SEED_PHRASE"], 0)
readme = "# Chat Protocol Adapter \nExample of how to integrate chat protocol."
endpoint = "AGENT_EXTERNAL_ENDPOINT"


app = FastAPI()


@app.get("/status")
async def healthcheck():
    return {"status": "OK - Agent is running"}


@app.post("/chat")
async def handle_message(env: Envelope):
    msg = parse_envelope(env, {ChatMessage, ChatAcknowledgement})
    if isinstance(msg, ChatMessage) and msg.text():
        print(f"Received message from {env.sender}: {msg.text()}")
        send_message_to_agent(
            destination=env.sender,
            msg=ChatMessage([TextContent("Thanks for the message!")]),
            sender=identity,
        )
