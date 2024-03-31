# Import libraries
import requests
import json
from uagents import Model, Protocol, Context
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field

# Define dictionary with country codes
country_codes = {
    "argentina": "ar", "australia": "au", "austria": "at", "belgium": "be", 
    "bulgaria": "bg", "brazil": "br", "canada": "ca", "china": "cn", 
    "colombia": "co", "cuba": "cu", "czech republic": "cz", "germany": "de", 
    "egypt": "eg", "france": "fr", "united kingdom": "gb", "greece": "gr", 
    "hong kong": "hk", "hungary": "hu", "indonesia": "id", "ireland": "ie", 
    "israel": "il", "india": "in", "italy": "it", "japan": "jp", 
    "south korea": "kr", "lithuania": "lt", "latvia": "lv", "morocco": "ma", 
    "mexico": "mx", "malaysia": "my", "nigeria": "ng", "netherlands": "nl", 
    "norway": "no", "new zealand": "nz", "philippines": "ph", "poland": "pl", 
    "portugal": "pt", "romania": "ro", "serbia": "rs", "russia": "ru", 
    "saudi arabia": "sa", "sweden": "se", "singapore": "sg", "slovenia": "si", 
    "slovakia": "sk", "thailand": "th", "turkey": "tr", "taiwan": "tw", 
    "ukraine": "ua", "united states": "us", "venezuela": "ve", "south africa": "za"
}
 
# Define the Generate News model
class GenerateNews(Model):
    country: str = Field(description='')
 
# Define function to generate regional news according to country
async def get_regional_news(country):
    api_key = 'NEWS-API API KEY'
    main_url = f"https://newsapi.org/v2/top-headlines?country={country_codes.get(country.lower())}&apiKey={api_key}"
    news = requests.get(main_url).json() 
    articles=news['articles'] #Returns all the articles from top to bottom
    for i in articles:
        top_most_url=i['url']
        break #Fetching the top most article url and then break the loop

    return top_most_url


 
# Define protocol for regional news generation Protocol
generate_news_reg_protocol = Protocol("Generate Regional News")
 
# Define a handler for the Regional News generation protocol
@generate_news_reg_protocol.on_message(model=GenerateNews, replies=UAgentResponse)
async def on_generate_news_request(ctx: Context, sender: str, msg: GenerateNews):
 
    ctx.logger.info(f"Received ticket request from {sender} with prompt: {msg.country}")
    try:
        # Get the country code from the country_code dictionary
        country_code = country_codes.get(msg.country.lower())
        # Generate news based on the requested country and log it on agentverse
        message = await get_regional_news(msg.country)
        ctx.logger.info(f"Message from endpoint: {message}")
        # Send a successful response with the generated news
        await ctx.send(sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL))
    # Handle any exceptions that occur during news generation
    except Exception as exc:
        ctx.logger.error(f"Error in getting top news article ka url: {exc}")
        # Send an error response with details of the encountered error
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Error in getting top new article ka url: {exc}",
                type=UAgentResponseType.ERROR
            )
        )
            
 
# Include the Generate Regional News protocol in your agent
agent.include(generate_news_reg_protocol)