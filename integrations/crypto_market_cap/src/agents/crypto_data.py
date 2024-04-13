from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
import uuid
from dotenv import load_dotenv
import os
import requests
from pydantic import BaseModel

class CryptoRequest(BaseModel):
    symbols: str

load_dotenv()

api_key = os.getenv('X_CMC_PRO_API_KEY')



crypto_protocol = Protocol("Crypto")

@crypto_protocol.on_message(model=CryptoRequest, replies=UAgentResponse)
async def get_crypto_data(ctx: Context, sender: str, msg: CryptoRequest):
    symbols = msg.symbols.replace(" ", "").upper()
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbols}"
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,  # replace 'your_api_key' with your actual API key
    }
    try:
        ctx.logger.info(f"Attempting to fetch data for {msg.symbols}")
        crypto_data = requests.get(url, headers=headers)
        crypto_data.raise_for_status()
        data = crypto_data.json()

        # Extract specific fields from the JSON response and format them as a string
        text_data = ""
        for symbol, crypto in data['data'].items():
            name = crypto['name']
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

        # Ask the user if they also want to see the top performing cryptocurrencies
        await ctx.send(
            sender,
            UAgentResponse(
                message="Do you also want to see the top performing cryptocurrencies?",
                type=UAgentResponseType.QUESTION,
                request_id=request_id,
                options=["Yes", "No"]
            ),
        )
        
    except Exception as exc:
        ctx.logger.info(f"Error during Crypto Data retrieval: {exc}")
        return None

crypto_agent = Agent()
crypto_agent.include(crypto_protocol)