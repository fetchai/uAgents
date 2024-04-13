# Importing libraries
import requests
from uagents import Agent, Model, Context, Protocol
import requests
import json
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

#Define a model for the message sent by the user to the agent
class book_name(Model):
    genre: str = Field(description="What is the genre you are intrested in?")

#Defining a protocol 
book_agent_protocol = Protocol("BookAgent Protocol")

#Book recommendation function
def search_books_by_genre(genre):
    base_url = "http://openlibrary.org/subjects/"
    url = base_url + genre.lower() + ".json?limit=10"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'works' in data and len(data['works']) > 0:
            books_details = [f"{i+1}. {work['title']} (Authors: {', '.join([author['name'] for author in work['authors']])})" 
                             for i, work in enumerate(data['works']) if 'title' in work and 'authors' in work]
            return "Top 10 books in the " + genre + " genre:\n" + "\n".join(books_details)
        else:
            return f"No books found in the {genre} genre."
    else:
        return "Failed to fetch books from the API."
            
#Event handler for handling responses
@book_agent_protocol.on_message(model=book_name, replies={UAgentResponse})
async def Say_Joke(ctx: Context, sender: str, msg: book_name):
    result=search_books_by_genre(msg.genre)
    await ctx.send(sender, UAgentResponse(message=result,type=UAgentResponseType.FINAL))
    

agent.include(book_agent_protocol, publish_manifest=True)