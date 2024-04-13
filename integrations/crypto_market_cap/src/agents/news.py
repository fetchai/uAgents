from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
import uuid
import requests
import os
from dotenv import load_dotenv

load_dotenv()
class TopGrowthRequest(Model):
    pass

crypto_protocol = Protocol("Crypto")

@crypto_protocol.on_message(model=TopGrowthRequest, replies=UAgentResponse)
async def get_top_growth(ctx: Context, sender: str, msg: TopGrowthRequest):
    try:
        # Fetch news data
        api_key = os.getenv('NEWS_API_KEY')
        news_url = "https://newsdata.io/api/1/news?apikey={api_key}&q=BTC,ETH&language=en"
        ctx.logger.info("Attempting to fetch news data...")
        news_data = requests.get(news_url)
        news_data.raise_for_status()
        data = news_data.json()
        ctx.logger.info(data)

        # Extract titles and links of the top 5 articles
        articles = data['results'][:5]
        text_data = ""
        for article in articles:
            title = article['title']
            link = article['link']

            text_data += f"Title: {title}\nLink: {link}\n\n"

        ctx.logger.info(text_data)
        # Send the response
        request_id = str(uuid.uuid4())
        await ctx.send(
            sender,
            UAgentResponse(
                message=text_data,
                type=UAgentResponseType.FINAL,
                request_id=request_id
            ),
        )

    except Exception as exc:
        ctx.logger.error(f"Error during news data retrieval: {exc}")
        return None

agent = Agent()
agent.include(crypto_protocol)