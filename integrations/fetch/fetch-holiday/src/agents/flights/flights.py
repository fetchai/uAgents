from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
import requests
from messages import Flights, UAgentResponse, UAgentResponseType, KeyValue
import os
import uuid


FLIGHTS_SEED = os.getenv("FLIGHTS_SEED", "flights really secret phrase :)")

agent = Agent(
    name="flights_adaptor",
    seed=FLIGHTS_SEED
)

fund_agent_if_low(agent.wallet.address())

RAPIDAPI_API_KEY = os.environ.get("RAPIDAPI_API_KEY", "")

assert RAPIDAPI_API_KEY, "RAPIDAPI_API_KEY environment variable is missing from .env"

SKY_SCANNER_URL = "https://skyscanner-api.p.rapidapi.com/v3e/flights/live/search/synced"
headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": RAPIDAPI_API_KEY,
    "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com"
  }

def skyscanner_format_data(data):
  r = data["content"]["results"]
  carriers = r["carriers"]
  itineraries = r["itineraries"]
  segments = r["segments"]
  sorted_itineraries = data["content"]["sortingOptions"]["cheapest"]
  results = []
  for o in sorted_itineraries:
    _id = o["itineraryId"]
    it = itineraries[_id]
    for option in it["pricingOptions"]:
      price = option["price"]["amount"]
      if len(option["items"]) != 1:
        continue
      fares = option["items"][0]["fares"]
      if len(fares) != 1:
        continue
      segment_id = fares[0]["segmentId"]
      seg = segments[segment_id]
      carrier = carriers[seg["marketingCarrierId"]]
      duration = seg["durationInMinutes"]
      departure = seg["departureDateTime"]
      arrival = seg["arrivalDateTime"]
      results.append({
        "price": price,
        "duration": duration,
        "departure": departure,
        "arrival": arrival,
        "carrier": carrier
      })
  return results

def skyscanner_top5(fares):
  return [fares[i] for i in range(len(fares)) if i < 5]

flights_protocol = Protocol("Flights")

@flights_protocol.on_message(model=Flights, replies={UAgentResponse})
async def flight_offers(ctx: Context, sender: str, msg: Flights):
    ctx.logger.info(f"Received message from {sender}, session: {ctx.session}")

    dept_year, dept_month, dept_day = msg.date.split("-")
    payload = {
         "query": {
            "market": "UK",
            "locale": "en-GB",
            "currency": "GBP",
            "queryLegs": [
                {
                    "originPlaceId": {"iata": msg.from_},
                    "destinationPlaceId": {"iata": msg.to},
                    "date": {
                        "year": int(dept_year),
                        "month": int(dept_month),
                        "day": int(dept_day)
                    }
                }
            ],
            "cabinClass": "CABIN_CLASS_ECONOMY",
            "adults": msg.persons
	    }
    }
    print("CALLING SKYSCANNER, payload ", payload)
    try:
        response = requests.request("POST", SKY_SCANNER_URL, json=payload, headers=headers)
        if response.status_code != 200:
            print("SKYSCANNER STATUS CODE not 200: ", response.json())
            await ctx.send(sender, UAgentResponse(message=response.text, type=UAgentResponseType.ERROR))
            return
        formatted = skyscanner_format_data(response.json())
        top5 = skyscanner_top5(formatted)
        print("SKYSCANNER TOP5 RESPONSE: ", top5)
        request_id = str(uuid.uuid4())
        options = []
        for idx, o in enumerate(top5):
            dep = f"{o['departure']['hour']:02}:{o['departure']['minute']:02}"
            arr = f"{o['arrival']['hour']:02}:{o['arrival']['minute']:02}"
            option = f"""{o["carrier"]["name"]} for £{o['price']},  {dep} - {arr}, flight time {o['duration']} min"""
            options.append(KeyValue(key=idx, value=option))
        await ctx.send(sender, UAgentResponse(options=options, type=UAgentResponseType.SELECT_FROM_OPTIONS, request_id=request_id))
    except Exception as exc:
         ctx.logger.error(exc)
         await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))

agent.include(flights_protocol)
