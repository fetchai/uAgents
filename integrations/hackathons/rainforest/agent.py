# Here we demonstrate how we can create a DeltaV compatible agent responsible for getting Amazon Product from Rainforest
# API. After running this agent, it can be registered to DeltaV on Agentverse's Services tab. For registration,
# you will have to use the agent's address.
#
# third party modules used in this example
import requests
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType


# Define the updated Rainforest API protocol
class SearchAmazonRequest(Model):
    search_term: str = Field(description="Describes the text field to query for a product to search in marketplace")


# Define the Rainforest API details
rainforest_base_url = "https://api.rainforestapi.com/request"

rainforest_protocol = Protocol("Rainforst Protocol")


# Function to extract top 5 products from the search results
def extract_top_5_products(data) -> list or None:
    """
    Extracts all the Search Results from the API Response

    Returns:
        List of top 5 Products.
    """
    products = data.get("search_results", [])  # Extract top 5 results
    enriched_products = []
    index = 1
    for product_info in products:
        if len(enriched_products) <= 5:
            if product_info.get('price'):
                enriched_product = (
                    f"{index}. Title: {product_info.get('title')}\n"
                    f"   ASIN: {product_info.get('asin')}\n"
                    f"   Link: <a href={product_info.get('link')}>Product Link</a>\n"
                    f"   Rating: {product_info.get('rating')}\n"
                    f"   Price: {product_info.get('price').get('raw')}\n"
                )
                enriched_products.append(enriched_product)
                index += 1
            else:
                continue
        else:
            break
    return '\n\n'.join(enriched_products)


# Function to perform a search on Amazon using the Rainforest API
def search_amazon_products(search_term):
    """
    Retrieves data from the Rainforest API for Amazon Products.
    Args:
        search_term: search term for product.

    Returns:
        list or None: A list of Amazon product data if successful, or None if the request fails.
    """
    params = {
        'api_key': API_KEY,
        'type': 'search',
        'amazon_domain': 'amazon.co.uk',
        'search_term': search_term + ' above 100',
        'output': 'json'
    }

    response = requests.get(rainforest_base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None

@rainforest_protocol.on_query(model=SearchAmazonRequest, replies=UAgentResponse)
async def search_amazon_q(ctx: Context, sender: str, msg: SearchAmazonRequest):
    ctx.logger.info(f"Received message from {sender} to search Amazon for '{msg.search_term}'")
    try:
        data = search_amazon_products(msg.search_term)

        if data is not None:
            top_5_products = extract_top_5_products(data)
            await ctx.send(sender, UAgentResponse(
                message=top_5_products,
                type=UAgentResponseType.FINAL,
            ))
        else:
            await ctx.send(sender, UAgentResponse(
                message="Please try some other query, could not find any result for the given search query.",
                type=UAgentResponseType.FINAL,
            ))
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(sender, UAgentResponse(
            message="Facing some trouble while finding the product from amazon, please try again after some time",
            type=UAgentResponseType.FINAL,
        ))


# Include the updated Rainforest API protocol in the agent
agent.include(rainforest_protocol)