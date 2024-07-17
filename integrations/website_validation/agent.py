import os

from ai_engine import UAgentResponse, UAgentResponseType
from dotenv import load_dotenv
from uagents import Agent, Context, Field, Model, Protocol
from uagents.setup import fund_agent_if_low

from grammer_check_agent_helper import (find_content_grammar_mistakes,
                                        scrape_website)
from utils import find_broken_links, format_errors

load_dotenv()

AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")

agent = Agent(
    name="website validation",
    seed="website validation phrase",
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

protocol = Protocol("website validation versions", version="0.1.1")

fund_agent_if_low(agent.wallet.address())

print(agent.address, "agent_address")


class WebsiteValidationInput(Model):
    website_url: str = Field(
        description="Describes the field where user provide the Website link that user want to find for website validation"
    )


@protocol.on_message(model=WebsiteValidationInput, replies={UAgentResponse})
async def message_handler(ctx: Context, sender: str, msg: WebsiteValidationInput):
    ctx.logger.info(f"Received webiste {sender} url: {msg.website_url}.")
    try:
        broken_links, invalid_links = find_broken_links(url=msg.website_url)
        scrapped_content = scrape_website(url=msg.website_url)
        grammar_mistakes = find_content_grammar_mistakes(content=scrapped_content)

        if scrapped_content and grammar_mistakes:
            res = format_errors(grammar_mistakes)
            result = ""
            if not broken_links or not invalid_links:
                result = f"No broken links found for {msg.website_url}\n Grammer mistake:\n {res}\n"
                await ctx.send(
                    sender,
                    UAgentResponse(message=result, type=UAgentResponseType.FINAL),
                )
            else:
                result = f"Broken links: {broken_links} and Invalid links: {invalid_links}\n Grammer mistake:\n {res}\n"
                await ctx.send(
                    sender,
                    UAgentResponse(message=result, type=UAgentResponseType.FINAL),
                )
        else:
            result = f"No data found for {msg.website_url}"
            await ctx.send(
                sender, UAgentResponse(message=result, type=UAgentResponseType.FINAL)
            )
    except Exception as e:
        ctx.logger.error(f"Somethig went wrong while finding borken links. {e}")
        result = "Somethig went wrong while finding borken links."
        await ctx.send(
            sender, UAgentResponse(message=result, type=UAgentResponseType.ERROR)
        )


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
