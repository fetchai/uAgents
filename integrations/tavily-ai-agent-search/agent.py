import requests
from ai_engine import UAgentResponse, UAgentResponseType

# Define the Search Request model
class SearchRequest(Model):
    query: str

# Define the protocol for Tavily Search
tavily_search_protocol = Protocol("Tavily Search")

def tavily_search(query, API_KEY):
    """Perform a search using the Tavily Search API and return results."""
    endpoint = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "API_KEY": API_KEY,
        "query": query,
        "search_depth": "basic",
        "include_images":False, 
        "include_answer":False, 
        "include_raw_content":False, 
        "max_results":5, 
        "include_domains":None, 
        "exclude_domains":None
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        ctx.logger.info(f"Error during Tavily search: {e}")
        return None

# Function to format the results into a simple string
def format_results(results):
    formatted_string = f"Query: {results['query']}\n"
    for result in results['results']:
        formatted_string += f"Title: {result['title']}\nURL: {result['url']}\nContent: {result['content']}\n\n"
    return formatted_string.strip()

@tavily_search_protocol.on_message(model=SearchRequest, replies=UAgentResponse)
async def on_search_request(ctx: Context, sender: str, msg: SearchRequest):
    ctx.logger.info(f"Received search request from {sender} with query: {msg.query}")

    try:
        # Perform the search
        search_results = tavily_search(msg.query, API_KEY)
        if search_results is None:
            raise Exception("Failed to get search results.")

        # Send the search results response
        formatted_string = format_results(search_results)
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"{formatted_string}",  # You may format this as needed
                type=UAgentResponseType.FINAL  # Assuming FINAL indicates a successful response
            )
        )

    except Exception as exc:
        ctx.logger.error(f"An error occurred: {exc}")
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Error: {exc}",
                type=UAgentResponseType.ERROR  # Assuming ERROR indicates an error response
            )
        )

# Include the Tavily Search protocol in your agent
agent.include(tavily_search_protocol)
