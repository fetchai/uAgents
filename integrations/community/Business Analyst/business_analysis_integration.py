# Import Required Libraries
import json
import requests
import openai
from textblob import TextBlob
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

# Set your API keys
ALPHA_VANTAGE_API_KEY = 'YOUR_ALPHA_VANTAGE_API_KEY'
GNEWS_API_KEY = 'YOUR_GNEWS_API_KEY'
OPENAI_API_KEY = 'YOUR_OPEN_AI_API_KEY'

# Define the request model for your business analysis
class BusinessAnalysisRequest(Model):
    company_name: str = Field(description="Enter the company name for which you want to perform business analysis:")

# Initialize your agent
SEED_PHRASE = "Business Analysis Seed Phrase"
AGENT_MAILBOX_KEY = "YOUR_MAILBOX_KEY"
businessAnalysisAgent = Agent(
    name="Business Analysis Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)
print(businessAnalysisAgent.address)
# Fund the agent if needed
fund_agent_if_low(businessAnalysisAgent.wallet.address())

# Define a protocol for handling business analysis requests
businessAnalysisProtocol = Protocol("Business Analysis Protocol")

# Define helper functions
async def fetch_symbol(company_name):
    """Fetch the stock symbol for the company using Alpha Vantage."""
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    print(response)
    if response.status_code == 200:
        data = response.json()
        print(data)
        # Typically, the best match will be the first item in the bestMatches list
        if data.get('bestMatches') and len(data['bestMatches']) > 0:
            # Return the symbol of the best match
            Symbol = data['bestMatches'][0]['1. symbol']
            return Symbol
    else:
        return 'No Symbol found'

async def fetch_financial_data(symbol):
    """Fetch financial data for the symbol using Alpha Vantage."""
    url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url).json()
    # Select the last 10 years of financial data
    return response['annualReports'][:10] if 'annualReports' in response else []

async def analyze_news(company_name):
    """Analyze news sentiment for the company using GNews and TextBlob."""
    url = f"https://gnews.io/api/v4/search?q={company_name}&token={GNEWS_API_KEY}&lang=en"
    articles = requests.get(url).json().get('articles', [])
    combined_text = ' '.join([f"{article['title']}: {article.get('description', '')}" for article in articles])
    analysis = TextBlob(combined_text)
    # Return both sentiment analysis and combined news text
    return analysis.sentiment.polarity, analysis.sentiment.subjectivity, combined_text

async def generate_analysis(financial_data, news_sentiment, news_content):
    """Generate business analysis using OpenAI."""
    openai.api_key = OPENAI_API_KEY
    messages = [
        {"role": "system", "content": "You are a knowledgeable business analyst."},
        {"role": "user", "content": f"Analyze the financial data and news sentiment for a company. Financial data: {json.dumps(financial_data, indent=2)}. News sentiment: {news_sentiment}. News content: {news_content}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=1000
    )
    return response.choices[0].message['content'] if response.choices else "Analysis not provided."


# Define the behavior when a message is received
@businessAnalysisProtocol.on_message(model=BusinessAnalysisRequest, replies={UAgentResponse})
async def handle_business_analysis_request(ctx: Context, sender: str, msg: BusinessAnalysisRequest):
    ctx.logger.info(msg.company_name)
    symbol = await fetch_symbol(msg.company_name)
    ctx.logger.info(symbol)
    financial_data = await fetch_financial_data(symbol)
    ctx.logger.info(financial_data)
    polarity, subjectivity, news_content = await analyze_news(msg.company_name)
    ctx.logger.info(news_content)
    analysis = await generate_analysis(financial_data, (polarity, subjectivity), news_content)
    ctx.logger.info(analysis)
    await ctx.send(sender, UAgentResponse(message=analysis, type=UAgentResponseType.FINAL))

# Start the agent
businessAnalysisAgent.include(businessAnalysisProtocol, publish_manifest=True)
businessAnalysisAgent.run()
