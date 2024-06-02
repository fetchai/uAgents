from contextvars import Context
from pydantic import BaseModel
from typing import Protocol
import requests
from ai_engine import UAgentResponse, UAgentResponseType
import logging

class GasPriceRequest(BaseModel):
    chain_id: int  # Chain ID represented as an integer

class GasPriceProtocol(Protocol):
    async def on_gas_price_request(self, ctx: Context, sender: str, msg: GasPriceRequest): ...

# Define the API key (replace with your actual key)
API_KEY = ""

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def fetch_gas_prices(chain_id):
    """Fetch gas prices from Infura API."""
    url = f'https://gas.api.infura.io/networks/{str(chain_id)}/suggestedGasFees'
    headers = {
        "Authorization": f"Basic {API_KEY}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.info(f"Error during Infura gas price retrieval: {exc}")
        return None

def format_gas_price_results(results):
    formatted_string = "🔥 Gas Price Summary:\n"
    for level in ['low', 'medium', 'high']:
        gas_info = results[level]
        formatted_string += (
            f"Level: {level.capitalize()}\n"
            f"🚀 Max Priority Fee: {gas_info['suggestedMaxPriorityFeePerGas']} Gwei\n"
            f"💸 Max Fee: {gas_info['suggestedMaxFeePerGas']} Gwei\n\n"
        )
    formatted_string += (
        f"🔧 Estimated Base Fee: {results['estimatedBaseFee']} Gwei\n"
        f"📊 Network Congestion: {results['networkCongestion']}\n"
        f"⬆️ Priority Fee Trend: {results['priorityFeeTrend']}\n"
        f"⬇️ Base Fee Trend: {results['baseFeeTrend']}\n"
    )
    return formatted_string.strip()

class SimpleAgent:
    def __init__(self):
        self.protocols = []
        self.logger = logger

    def include(self, protocol):
        self.protocols.append(protocol)

    async def send(self, recipient, response):
        # Simulate sending a response
        print(f"Sending to {recipient}: {response.message}")

    async def on_gas_price_request(self, ctx: Context, sender: str, msg: GasPriceRequest):
        # Log the incoming request
        self.logger.info(f"Received gas price request for chain ID: {msg.chain_id} from {sender}")

        try:
            # Fetch gas prices
            gas_prices = fetch_gas_prices(msg.chain_id)
            if gas_prices is None:
                # Send the error response
                await self.send(
                    sender,
                    UAgentResponse(
                        message=(
                            f"⚠️ Error: Unable to fetch gas prices for chain ID: {msg.chain_id}.\n\n"
                            "Please make sure the chain ID is correct.\n"
                            "If yes, then there might be something wrong with the API/agent. "
                            "Please try again later."
                        ),
                        type=UAgentResponseType.ERROR
                    )
                )
                return

            # Format and log the response
            formatted_string = format_gas_price_results(gas_prices)
            self.logger.info(f"Sending gas price information for chain ID: {msg.chain_id} to {sender}\n{formatted_string}")

            # Send the response
            await self.send(
                sender,
                UAgentResponse(
                    message=f"{formatted_string}",
                    type=UAgentResponseType.FINAL
                )
            )

        except Exception as exc:
            error_message = f"An error occurred while processing request for chain ID: {msg.chain_id} - {exc}"
            self.logger.error(error_message)

            # Send the error response
            await self.send(
                sender,
                UAgentResponse(
                    message=f"Error: An error occurred while processing request for chain ID: {msg.chain_id}",
                    type=UAgentResponseType.ERROR
                )
            )

# Instantiate the agent and include the protocol
agent = SimpleAgent()
agent.include(GasPriceProtocol)

# Simulate a request (For testing purposes)
import asyncio

async def simulate_request():
    ctx = Context()
    request = GasPriceRequest(chain_id=1)
    await agent.on_gas_price_request(ctx, "test_sender", request)

asyncio.run(simulate_request())
