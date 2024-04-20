import requests
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Model, Field
import os
from dotenv import load_dotenv

load_dotenv()

Flight_API_KEY = os.getenv("Flight_API_KEY")

flights_protocol = Protocol(name="flights_protocol")

class Flights(Model):
    src: str = Field(
        description="Name of the city or airport from where the user wants to book the flight."
    )
    dest: str = Field(
        description="Name of the city or airport of the destination of the flight."
    )
    date: str = Field(
        description="Date for flight departure, the date on which the user wants to book the flight."
    )
    person: int = Field(
        description="Number of passengers the user wants to book for."
    )

def fetch_airport_info(location):
    url = "https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchAirport"

    querystring = {"query": location}

    headers = {
        "X-RapidAPI-Key": "Flight_API_KEY",
        "X-RapidAPI-Host": "sky-scrapper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    
    if data["status"]:
        return data["data"][0]["skyId"], data["data"][0]["navigation"]["entityId"]
    else:
        return None, None

carriers = []

def format_data(data):
    airports_data = data['filterStats']
    src_airports = [airport['name'] for airport in airports_data['airports'][0]["airports"]]
    des_airports = [airport['name'] for airport in airports_data['airports'][1]["airports"]]

    duration = "minimum time => {min_duration} mins \nmaximum time => {max_duration} mins".format(
        min_duration=airports_data['duration']['min'],
        max_duration=airports_data['duration']['max']
    )
    stopPrices = data['filterStats']['stopPrices']['direct']['formattedPrice']
    price = "\nPrice for Direct Flight => {}".format(stopPrices)

    for items in airports_data['carriers']:
        carriers.append(items['name'])

    return "Source Airports: {}\nDestination Airports: {}\nDuration: {}\nPrice: {}".format(
        ", ".join(src_airports),
        ", ".join(des_airports),
        duration,
        price
    ) + "\ncarriers=>\n" + "\n".join(carriers)


def fetch_flight(src, dest, date, person):
    src_skyId, src_entityId = fetch_airport_info(src)
    dest_skyId, dest_entityId = fetch_airport_info(dest)

    if src_skyId is None or dest_skyId is None:
        return "Unable to fetch airport information. Please check the location names and try again."

    url = "https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlights"

    querystring = {
        "originSkyId": src_skyId,
        "destinationSkyId": dest_skyId,
        "originEntityId": src_entityId,
        "destinationEntityId": dest_entityId,
        "date": date,
        "adults": person,
        "currency": "USD",
        "market": "en-US",
        "countryCode": "US"
    }

    headers = {
        "X-RapidAPI-Key": "1dc3581a84mshdcf979fd41a22a8p1bcc2ajsnd841021890c1",
        "X-RapidAPI-Host": "sky-scrapper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    return response.json()

@flights_protocol.on_message(model=Flights, replies={UAgentResponse})
async def flight_offers(ctx: Context, sender: str, msg: Flights):
    time = "-".join(msg.date.split(".")[::-1])
    response = fetch_flight(msg.src, msg.dest, time, msg.person)
    data = format_data(response['data'])  # Assuming you have a format_data function
    await ctx.send(sender, UAgentResponse(message=data, type=UAgentResponseType.FINAL))

agent.include(flights_protocol)
