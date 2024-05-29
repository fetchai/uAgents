from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
import logging, aiohttp, logging, asyncio, fitz, requests, json, urllib.parse 
import openai
import xml.etree.ElementTree as ET
from motor.motor_asyncio import AsyncIOMotorClient


class TopicRequest(Model):
    topic_name: str = Field(description="Enter the name of the topic for which you want to fetch research paper:")


SEED_PHRASE = "Responsible AI Paper Fetch Seed Phrase"
AGENT_MAILBOX_KEY = "YOUR_MAILBOX_KEY"
OPENAI_API_KEY = 'YOUR_OPEN_AI_API_KEY'


Ragent = Agent(
    name="Resonsible AI Paper Fetch Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

print(Ragent.address)


# Fund the agent if needed
fund_agent_if_low(Ragent.wallet.address())


# Define a protocol for handling business analysis requests
RagentProtocol = Protocol("Responsible AI Paper Fetch Protocol")

# Define helper functions
async def fetch_paper(topic_name):
    """Fetch the research paper on the given topic using arXiv public API"""
    encoded_query = urllib.parse.quote(topic_name)
    base_url = 'http://export.arxiv.org/api/query?search_query=all:'
    start_index = 0
    max_results = 1

    try:
        url = f'{base_url}{encoded_query}&start={start_index}&max_results={max_results}'
        logging.info(f'Fetching URL: {url}')

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    logging.error(f'Error fetching data: HTTP {response.status}')
                    return None

                data = await response.text()
                logging.debug(f'Response data: {data}')

                try:
                    root = ET.fromstring(data)
                    entries = root.findall('{http://www.w3.org/2005/Atom}entry')

                    for entry in entries:
                        paper_title = entry.find('{http://www.w3.org/2005/Atom}title').text
                        paper_summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                        authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')]
                        pdf_link_element = entry.find('{http://www.w3.org/2005/Atom}link[@type="application/pdf"]')
                        paper_link = pdf_link_element.attrib.get('href') if pdf_link_element is not None else None
                        
                        paper_content = None
                        if paper_link:
                            paper_content = await fetch_pdf_content(paper_link)

                        paper_details = json.dumps({
                            "title": paper_title,
                            "summary": paper_summary,
                            "authors": authors,
                            "link": paper_link,
                            "content": paper_content
                        })


                    logging.info(f'Successfully fetched and stored {len(entries)} papers for query: {topic_name}')
                    return entries
                
                except ET.ParseError as e:
                    logging.error("Error parsing XML data", exc_info=True)
                    logging.error(f'Parsing error: {e}')
                    return None

    except aiohttp.ClientError as e:
        logging.error("Error fetching data", exc_info=True)
        logging.error(f'Client error: {e}')
        return None
    
    except asyncio.TimeoutError as e:
        logging.error("Request timed out", exc_info=True)
        logging.error(f'Timeout error: {e}')
        return None


async def get_paper_details(topic_name):
    paper_json = await fetch_paper(topic_name)
    if paper_json is None:
        return None
    
    paper = json.loads(paper_json)
    return {
        "title": paper.get('title'),
        "summary": paper.get('summary'),
        "authors": paper.get('authors'),
        "link": paper.get('link'),
        "content": paper.get('content')
    }


async def fetch_pdf_content(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        
        with open("temp.pdf", "wb") as f:
            f.write(response.content)

        doc = fitz.open("temp.pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        
        return text
    except Exception as e:
        logging.error(f"Error fetching or parsing PDF content: {e}", exc_info=True)
        return None
    



async def paper_summary(paper_content):
    """Generate a summary of the research paper."""
    messages = [
        {"role": "system", "content": "You are a knowledgeable AI research assistant."},
        {"role": "user", "content": f"Summarize the following research paper content: {paper_content}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=500
    )
    return response.choices[0].message['content'] if response.choices else "Summary not provided."


# Define the behavior when a message is received
@RagentProtocol.on_message(model=TopicRequest, replies={UAgentResponse})
async def handle_topic_request(ctx: Context, sender: str, msg: TopicRequest):
    ctx.logger.info(msg.topic_name)
    
    paper_details = await get_paper_details(msg.topic_name)
    if paper_details:
        title = paper_details.get('title')
        summary = paper_details.get('summary')
        authors = paper_details.get('authors')
        link = paper_details.get('link')
        content = paper_details.get('content')
        
        if title and authors and link:
            logging.info(f"Title: {title}")
            logging.info(f"Authors: {', '.join(authors)}")
            logging.info(f"Link: {link}")
        
        paper_summary_text = await paper_summary(content)
        ctx.logger.info(paper_summary_text)

        await ctx.send(sender, UAgentResponse(message=paper_summary_text, type=UAgentResponseType.FINAL))
    else:
        ctx.logger.error("Failed to fetch paper details.")
        await ctx.send(sender, UAgentResponse(message="Failed to fetch paper details.", type=UAgentResponseType.FINAL))



Ragent.include(RagentProtocol, publish_manifest=True)
Ragent.run()


