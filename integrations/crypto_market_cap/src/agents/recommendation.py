from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
import uuid
import requests
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('X_CMC_PRO_API_KEY')

class TopGrowthRequest(Model):
    pass

crypto_protocol = Protocol("Crypto")

@crypto_protocol.on_message(model=TopGrowthRequest, replies=UAgentResponse)
async def get_top_growth(ctx: Context, sender: str, msg: TopGrowthRequest):
    """Fetch top growing cryptocurrencies from CoinMarketCap API."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,  # replace 'your_api_key' with your actual API key
    }
    try:
        ctx.logger.info(f"Attempting to fetch top growing cryptocurrencies")
        crypto_data = requests.get(url, headers=headers)
        crypto_data.raise_for_status()
        data = crypto_data.json()

        # Sort the cryptocurrencies by the percentage change in the last 24 hours in descending order
        sorted_cryptos = sorted(data['data'], key=lambda crypto: crypto['quote']['USD']['percent_change_24h'], reverse=True)

        # Get the top 10 cryptocurrencies
        top_10_cryptos = sorted_cryptos[:10]

        # Format the data for display
        text_data = ""
        for crypto in top_10_cryptos:
            name = crypto['name']
            symbol = crypto['symbol']
            price = crypto['quote']['USD']['price']
            volume_24h = crypto['quote']['USD']['volume_24h']
            percent_change_24h = crypto['quote']['USD']['percent_change_24h']
            market_cap = crypto['quote']['USD']['market_cap']

            text_data += f"Name: {name}, Symbol: {symbol}, Price: {price}, Volume (24h): {volume_24h}, Change (24h): {percent_change_24h}%, Market Cap: {market_cap}\n"

        ctx.logger.info(text_data)
        request_id = str(uuid.uuid4())
        ctx.logger.info("test1")
   
        await ctx.send(
            sender,
            UAgentResponse(
                message=text_data,
                type=UAgentResponseType.FINAL,
                request_id=request_id
            ),
        )
        
        
    except Exception as exc:
        ctx.logger.info(f"Error during Crypto Data retrieval: {exc}")
        return None

agent.include(crypto_protocol)