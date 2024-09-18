import requests
from ai_engine import UAgentResponse, UAgentResponseType


class GasPriceRequest(Model):
    chain_id: int  # Chain ID represented as an integer


gas_price_protocol = Protocol("Infura Gas Price Retrieval")

"""
import base64
api_key = 
api_key_secret = 
credentials = f"{api_key}:{api_key_secret}"
base64.b64encode(credentials.encode()).decode()
"""


def fetch_gas_prices(chain_id, ctx):
    """Fetch gas prices from Infura API."""
    url = f"https://gas.api.infura.io/networks/{str(chain_id)}/suggestedGasFees"
    headers = {"Authorization": f"Basic {API_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        ctx.logger.info(f"Error during Infura gas price retrieval: {exc}")
        return None


def format_gas_price_results(results):
    formatted_string = "🔥 Gas Price Summary:\n"
    for level in ["low", "medium", "high"]:
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


@gas_price_protocol.on_message(model=GasPriceRequest, replies=UAgentResponse)
async def on_gas_price_request(ctx: Context, sender: str, msg: GasPriceRequest):
    # Log the incoming request
    ctx.logger.info(
        f"Received gas price request for chain ID: {msg.chain_id} from {sender}"
    )

    try:
        # Fetch gas prices
        gas_prices = fetch_gas_prices(msg.chain_id, ctx)
        if gas_prices is None:
            # Send the error response
            await ctx.send(
                sender,
                UAgentResponse(
                    message=(
                        f"⚠️ Error: Unable to fetch gas prices for chain ID: {msg.chain_id}.\n\n"
                        "Please make sure the chain ID is correct.\n"
                        "If yes, then there might be something wrong with the API/agent. "
                        "Please try again later."
                    ),
                    type=UAgentResponseType.ERROR,
                ),
            )

        # Format and log the response
        formatted_string = format_gas_price_results(gas_prices)
        ctx.logger.info(
            f"Sending gas price information for chain ID: {msg.chain_id} to {sender}\n{formatted_string}"
        )

        # Send the response
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"{formatted_string}", type=UAgentResponseType.FINAL
            ),
        )

    except Exception as exc:
        error_message = f"An error occurred while processing request for chain ID: {msg.chain_id} - {exc}"
        ctx.logger.error(error_message)

        # Send the error response
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Error: An error occurred while processing request for chain ID: {msg.chain_id}",
                type=UAgentResponseType.ERROR,
            ),
        )


agent.include(gas_price_protocol)
