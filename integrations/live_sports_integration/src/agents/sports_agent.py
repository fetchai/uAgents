# Importing libraries
import requests
from uagents import Agent, Model, Context, Protocol
from uagents.setup import fund_agent_if_low

# Assuming Message and Response models are defined elsewhere
from message.model import Response, Message

# Setting up the Live Sports Agent
sport_agent = Agent(
    name='Live Sports Agent',
    port=1123,
    seed='Sports Agent secret seed phrase',
    endpoint='http://localhost:1123/submit'
)

# Checking and funding the agent's wallet if the balance is low
fund_agent_if_low(sport_agent.wallet.address())

@sport_agent.on_event('startup')
async def address(ctx: Context):
    # Logging the agent's address upon startup
    ctx.logger.info(sport_agent.address)

def format_sport_name(sport_name):
    """
    Format the sport name input by the user to capitalize the first letter.
    """
    return sport_name.capitalize()

def fetch_events_for_sport(sport_name):
    """
    Fetch live event details for the specified sport and return as a formatted string.
    """
    # Choosing the API endpoint based on the sport
    url = "https://livescore-sports.p.rapidapi.com/v1/events/live" if sport_name == "Cricket" else "https://sportscore1.p.rapidapi.com/events/live"
    # Setting the query parameters based on the sport
    querystring = {"locale":"EN", "timezone":"0", "sport":"cricket"} if sport_name == "Cricket" else {"page":"1"}
    headers = {
        "X-RapidAPI-Key": "Your-RapidAPI-Key",
        "X-RapidAPI-Host": url.split("/")[2]
    }
    # Making the API request
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    # Processing the API response
    events_data = []
    if sport_name == "Cricket":
        # Specific processing for cricket data
        data = data['DATA'][0] if 'DATA' in data and len(data['DATA']) > 0 else None
        if data and 'EVENTS' in data:
            for match in data['EVENTS']:
                events_data.append(process_match_details(match))
    else:
        # Processing for other sports
        data = data['data'] if 'data' in data else []
        for event in data:
            if event['sport']['name'].lower() == sport_name.lower():
                events_data.append(process_match_details(event, is_cricket=False))
    
    # Returning formatted event details
    return "\n\n".join(events_data)

def process_match_details(match, is_cricket=True):
    """
    Process and format match details for display.
    """
    # Formatting details based on whether it's cricket or another sport
    if is_cricket:
        details = [
            f"Match: {match['HOME_TEAM'][0]['NAME']} vs {match['AWAY_TEAM'][0]['NAME']}",
            f"Status: {match.get('LONG_VERSION_OF_MATCH_STATUS', 'Status not provided')}",
            f"Description: {match.get('DESCRIBE_CURRENT_STATUS_OF_MATCH', 'No description')}"
        ]
    else:
        details = [
            f"Match: {match['home_team']['name']} vs {match['away_team']['name']}",
            f"Sport: {match['sport']['name']}",
            f"Score: {match['home_team']['name']} {match['home_score']['current']} - {match['away_team']['name']} {match['away_score']['current']}",
            f"League: {match['league']['name']}",
            f"Status: {match['status']}",
            f"Start Time: {match['start_at']}",
            f"Round: {match.get('round_info', {}).get('round', 'N/A') if match.get('round_info') else 'N/A'}"
        ]
    return "\n".join(details)

@sport_agent.on_message(model=Message, replies=Response)
async def handle_query(ctx: Context, sender: str, msg: Message):
    # Handling user queries for live sports events
    sport = msg.message
    formatted_sport_name = format_sport_name(sport)
    events_response = fetch_events_for_sport(formatted_sport_name)
    # Sending the fetched events response back to the user
    await ctx.send(sender, Response(response=events_response))
