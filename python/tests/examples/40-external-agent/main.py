import os
from typing import cast

from fastapi import FastAPI
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    TextContent,
)
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.utils.messages import parse_envelope, send_message_to_agent


name = "Test Agent Example"
identity = Identity.from_seed(os.environ["AGENT_SEED_PHRASE"], 0)
readme = "# Test Agent Readme\nJust a test agent supporting chat protocol."
endpoint = "AGENT_EXTERNAL_ENDPOINT"


app = FastAPI()


@app.get("/")
async def healthcheck():
    return {"status": "OK - Agent is running"}


@app.post("/")
async def handle_message(env: Envelope):
    msg = cast(ChatMessage, parse_envelope(env, ChatMessage))
    print(f"Received message from {env.sender}: {msg.text()}")
    send_message_to_agent(
        destination=env.sender,
        msg=ChatMessage([TextContent("Thanks for the message!")]),
        sender=identity,
    )
