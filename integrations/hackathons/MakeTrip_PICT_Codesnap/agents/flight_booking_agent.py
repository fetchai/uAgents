import requests
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import  Field
import os
from dotenv import load_dotenv

load_dotenv()

Flight_API_KEY = os.getenv("Flight_API_KEY")

flights_protocol = Protocol(name="flights_protocol")
book_flight_protocol = Protocol(name="BookFlight")

class Flights(Model):
    source: str = Field(
        description="name of source location of the user."
    )
    destination: str = Field(
        description="name of destination location. location where the user wants to go."
    )
    date: str = Field(
        description="date of flight departure."
    )
    person: int = Field(
        description="number of passengers the user wants to book for."
    )

class BookFlight(Model):
    bookquery : str = Field(description="takes the response from flight booking details system.")

def fetch_airport_info(location):
    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport"

    querystring = {"query": location}

    headers = {
        "X-RapidAPI-Key": "Flight_API_KEY",
        "X-RapidAPI-Host": "sky-scrapper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    print("data", data)
    print(data["data"][0]["skyId"], data["data"][0]["navigation"]["entityId"])
    return data["data"][0]["skyId"], data["data"][0]["navigation"]["entityId"]

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
        "X-RapidAPI-Key": "Flight_API_KEY",
        "X-RapidAPI-Host": "sky-scrapper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    print('response', response)
    return response.json()


def format_data(data):
    airports_data = data['filterStats']
    src_airports = airports_data['airports'][0]["city"]
    des_airports = airports_data['airports'][1]["city"]
    print(src_airports, des_airports)

    stopprices = airports_data['stopPrices']['direct']['formattedPrice']
    carriers = []

    for items in airports_data['carriers']:
        carriers.append(items['name'])

    return [f"{carrier} - {src_airports} to {des_airports} cost {stopprices}\n" for carrier in carriers]


@flights_protocol.on_message(model=Flights, replies={UAgentResponse})
async def flight_offers(ctx: Context, sender: str, msg: Flights):
    datenew = "-".join(msg.date.split(".")[::-1])
    ctx.logger.info(f"{msg.source}, {msg.destination}, {datenew}, {msg.person}")
    response = fetch_flight(msg.source, msg.destination, datenew, msg.person)
    ctx.logger.info(f"data response {response}")
    ctx.logger.info(f"{response['data']}")
    data = format_data(response['data'])  
    await ctx.send(sender, UAgentResponse(message=str(data), type=UAgentResponseType.FINAL))


@book_flight_protocol.on_message(model=BookFlight, replies=UAgentResponse)
async def book_hotel(ctx: Context, sender: str, msg: BookFlight):
    ctx.logger.info(f"Received booking message from {sender}")
    name = msg.bookquery
    ctx.logger.info(f"{name}")
    
    # url = 'https://twilio-vercel.vercel.app/sendsms'
    # myobj = {'phone': '+919860245752', message:f"{name} hotel booked successfully"}

    # x = requests.post(url, json = myobj)

    # print(x.text)

    await ctx.send(
                sender,
                UAgentResponse(
                    message=f"{name} booked successfully",
                    type=UAgentResponseType.FINAL,
                    public_manifest=True
                )
            )


agent.include(flights_protocol)
agent.include(book_flight_protocol)
