import requests
import os
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
from serpapi import GoogleSearch


def get_stock_summary(company_name, api_key):
    # Defining params for query
    params = {
        "engine": "google_finance",
        "q": company_name,
        "api_key": api_key
    }    
    # Send the GET request
    search = GoogleSearch(params)
    results = search.get_dict()
    # Check if the request was successful
    if results:
        if not total_results:
            return "Nothing was found for the query: " + company_name

        res = "\nQuery: " + company_name + "\n"
        # Extract information from the 'futures_chain' section if available
        if "futures_chain" in total_results:
            futures_chain = total_results.get("futures_chain", [])[0] if total_results.get("futures_chain") else {}
            stock = futures_chain.get("stock", "N/A")
            price = futures_chain.get("price", "N/A")
            percentage = futures_chain.get("price_movement", {}).get("percentage", "N/A")
            movement = futures_chain.get("price_movement", {}).get("movement", "N/A")
            res += f"Stock: {stock}\nPrice: {price}\nChange: {percentage}%\nMovement: {movement}\n"
        else:
            res += "No futures chain information available.\n"

        # Extract and format market information
        markets = total_results.get("markets", {})
        for region in ['us', 'europe', 'asia']:
            if region in markets:
                res += f"{region.capitalize()}: "
                res += f"Price = {markets[region][0].get('price', 'N/A')}, "
                res += f"Movement = {markets[region][0].get('price_movement', {}).get('movement', 'N/A')}\n"
        
        return res

# Define the request model for your business analysis
class GoogleFinanceRequest(Model):
    company_name: str = Field(description="Enter the company name for which you want to get stock details")

# Initialize your agent
SEED_PHRASE = "Google Finance Seed Phrase"
AGENT_MAILBOX_KEY = "<Your_agent_mailbox_key_here"
googleFinanceAgent = Agent(
    name="Google Finance Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)
print(googleFinanceAgent.address)
# Fund the agent if needed
fund_agent_if_low(googleFinanceAgent.wallet.address())

# Define a protocol for handling business analysis requests
googleFinanceProtocol = Protocol("Google Finance Protocol")

# Define the behavior when a message is received
@googleFinanceProtocol.on_message(model=GoogleFinanceRequest, replies={UAgentResponse})
async def handle_business_analysis_request(ctx: Context, sender: str, msg: GoogleFinanceRequest):
    ctx.logger.info(f'User has requested details for {msg.company_name}')
    api_key = os.getenv('MY_API_KEY')
    details = get_stock_summary(msg.company_name, api_key)
    ctx.logger.info(details)
    await ctx.send(sender, UAgentResponse(message=details, type=UAgentResponseType.FINAL))

# Start the agent
googleFinanceAgent.include(googleFinanceProtocol, publish_manifest=True)
googleFinanceAgent.run()
