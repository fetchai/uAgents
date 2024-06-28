import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Model, Context, Protocol


# Define the Generate Article Summary model
class GenerateArticleSummary(Model):
    url: str

# Define function to generate article summary
async def get_article_summary(url):
    api_url = "https://article-data-extraction-and-summarization.p.rapidapi.com/article"
    headers = {
        "X-RapidAPI-Key": "API KEY (Rapid API)",
        "X-RapidAPI-Host": "article-data-extraction-and-summarization.p.rapidapi.com"
    }
    params = {
        "url": url,
        "summarize": "true",
        "summarize_language": "auto"
    }
    response = requests.get(api_url, headers=headers, params=params)
    data = response.json()['article']['text']
    return data #Returns summarized text ocntent

# Define protocol for article summary generation
generate_article_summary_protocol = Protocol("Generate Article Summary")

# Define a handler for the Article Summary generation protocol
@generate_article_summary_protocol.on_message(model=GenerateArticleSummary, replies=UAgentResponse)
async def on_generate_article_summary_request(ctx: Context, sender: str, msg: GenerateArticleSummary):
    ctx.logger.info(f"Received article summary request from {sender} with URL: {msg.url}")
    try:
        # Get the article summary based on the provided URL
        summary = await get_article_summary(msg.url)
        ctx.logger.info(f"Summary from endpoint: {summary}")
        # Send a successful response with the generated article summary
        await ctx.send(sender, UAgentResponse(message=summary, type=UAgentResponseType.FINAL))
    except Exception as exc:
        ctx.logger.error(f"Error in generating article summary: {exc}")
        # Send an error response with details of the encountered error
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Error in generating article summary: {exc}",
                type=UAgentResponseType.ERROR
            )
        )

# Include the Generate Article Summary protocol in your agent
agent.include(generate_article_summary_protocol)
