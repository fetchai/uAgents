
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
from uagents import Agent, Protocol, Context, Model
import os
import requests


class ResearchPaperSummarizer(Model):
    text: str = Field(description="Enter the text: ")
    

summarizer_protocol = Protocol("ResearchPaperSummarizer")

@summarizer_protocol.on_message(model=ResearchPaperSummarizer, replies={UAgentResponse})
async def handle_request(ctx: Context, sender: str, msg: ResearchPaperSummarizer):
    model_name = "google/pegasus-xsum"
    HUGGING_FACE_TOKEN="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"
    url = f"https://api-inference.huggingface.co/models/{model_name}"
    headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}
    payload = {
        "inputs": msg.text,
        "parameters": {
            "min_length": 60,
            "max_length": 150,
            "num_beams": 4,
            "early_stopping": True,
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    summary = response.json()[0]["summary_text"]
    message1="Summary:\n"
    await ctx.send(
        sender, UAgentResponse(message=message1+summary, type=UAgentResponseType.FINAL)
    )

agent = Agent()
agent.include(summarizer_protocol, publish_manifest=True)