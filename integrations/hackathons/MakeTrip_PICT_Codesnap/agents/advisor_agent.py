from ai_engine import UAgentResponse, UAgentResponseType
import requests
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

Advisor_API_KEY = os.getenv("Advisor_API_KEY")

def advisor(query):
    url = "https://maps-data.p.rapidapi.com/searchmaps.php"

    headers = {
            "X-RapidAPI-Key": Advisor_API_KEY,
            "X-RapidAPI-Host": "maps-data.p.rapidapi.com"
        }
    querystring = {"query":"places to visit in "+query,
                   "limit":"20",
                   "country":"in",
                   "lang":"en"}
    
    response = requests.get(url, headers=headers, params=querystring)
    return(response.json())

 
travel_advisor_protocol = Protocol(name="TravelAdvisor")
 
class Request(Model):
    message: str = Field(description="name of destination user wants to visit.")


@travel_advisor_protocol.on_message(model=Request, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: Request):
    i = 0
    response = advisor(msg.message)
    result = [item['name'] for item in response['data']]
    refactored_data = [f"""● {name}\n""" for name in result]
    await ctx.send(sender, UAgentResponse(message=str(refactored_data), type=UAgentResponseType.FINAL))

    
agent.include(travel_advisor_protocol)