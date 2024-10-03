from uagents import Context
from uagents import Model, Protocol
from serpapi import GoogleSearch


class FlightQuery(Model):
    current_location: str
    destination_choice: str


class FlightResponse(Model):
    lowest_price: float


flight_proto = Protocol()


def get_flight_price(query: FlightQuery) -> float:
    params = {
        "engine": "google_flights",
        "departure_id": query.current_location,
        "arrival_id": query.destination_choice,
        "outbound_date": "2024-03-25",
        "return_date": "2024-03-26",
        "currency": "USD",
        "hl": "en",
        "api_key": "63eb1540fbc626c8cbd6894f1f41f38ade088d36ced30f934050dd261052652c",
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    prices = [flight["price"] for flight in results["best_flights"]]
    for flight in results["other_flights"]:
        prices.append(flight["price"])
    return min(prices)


@flight_proto.on_message(model=FlightQuery, replies=FlightResponse)
async def handle_flight_query(ctx: Context, sender: str, msg: FlightQuery):
    price = get_flight_price(msg)
    await ctx.send(sender, FlightResponse(lowest_price=price))
