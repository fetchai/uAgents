"""The Elderly Assistant agent enhances the safety of vulnerable individuals (e.g. with reduced mobility), utilising
Natural Language Processing (NLP) to scrutinise incoming telephone calls and analysing audio captured by an loT device
(e.g. Smart doorbell), providing an evaluation of potential security risks posed by callers on the phone / visitors to
the property - essentially whether to reject the call or allow the person in to the house, with the assumption that it
may be difficult to reach the phone / door.

Langchain is set up to ingest multi-format information (documents, calendar, emails etc.) about the state of the home
(uploaded via a .zip file in Delta-V) to inform the decisions the AI makes."""

import datetime

from uagents import Agent, Context, Protocol, Model
from pydantic import Field

from ai_engine import UAgentResponse, UAgentResponseType
import os
from analyser import SafetyAnalyser
from summariser import SafetySummariser
from uagents.setup import fund_agent_if_low

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

SEED_PHRASE = os.getenv("SEED_PHRASE")

print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")
API_KEY = os.getenv("OPENAI_API_KEY")

safety_agent = Agent(
    name="elderly-assistant",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

safety_protocol = Protocol("safety-analysis")


class SafetyRequest(Model):
    dialog_url: str = Field(
        description="This field requires a url of audio containing a telephone call or visitor to the home stating their intention for calling/ visiting. This field is required."
    )
    document_repo_url: str = Field(
        ...,
        description="This field describes a url to a zip file containing any documents, emails, letters, calendars etc. that provide context about the state of the home (dates when people are home, when visitors are expected), safety information, as well as previous entry attempts to the property (both good and malicious). This field is required.",
    )


@safety_protocol.on_message(model=SafetyRequest, replies=UAgentResponse)
async def handle_safety_request(ctx: Context, sender: str, message: SafetyRequest):
    safety_summariser = SafetySummariser()
    summary = safety_summariser.download_and_summarise(message.dialog_url)

    safety_analyser = SafetyAnalyser(message.document_repo_url)

    assessment = safety_analyser.assess_danger(
        f"The time is {datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}. {summary.Summary}"
    )

    response_message = f"Incident Assessment: {assessment}\nSummary: {summary.Summary}"

    await ctx.send(
        sender, UAgentResponse(message=response_message, type=UAgentResponseType.FINAL)
    )


# Include the protocol in the agent
safety_agent.include(safety_protocol, publish_manifest=True)


@safety_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("Safety Analysis System Activating...")
    fund_agent_if_low(str(safety_agent.wallet.address()))


def run():
    safety_agent.run()


if __name__ == "__main__":
    run()
