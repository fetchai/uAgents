from uagents import Agent, Context
from protocols.destination import (
    DestinationQuery,
    DestinationResponse,
)
from protocols.flight import (
    FlightQuery,
    FlightResponse,
)
from protocols.hotel import (
    HotelQuery,
    HotelResponse,
)


travel_agent_address = (
    "agent1qw50wcs4nd723ya9j8mwxglnhs2kzzhh0et0yl34vr75hualsyqvqdzl990"
)

user_agent = Agent(
    name="user_agent",
    port=8003,
    seed="user_agent_secret_phrase",
    endpoint=["http://127.0.0.1:8003/submit"],
)


def get_user_input():
    budget = int(input("Enter your budget: "))
    activities = input("Enter activities (comma-separated): ").split(",")
    interests = input("Enter interests (comma-separated): ").split(",")
    return DestinationQuery(budget=budget, activities=activities, interests=interests)


@user_agent.on_interval(period=100, messages={DestinationQuery})
async def send_destination_query(ctx: Context):
    query = get_user_input()
    await ctx.send(travel_agent_address, query)


@user_agent.on_message(model=DestinationResponse, replies={FlightQuery})
async def handle_destination_response(
    ctx: Context, sender: str, msg: DestinationResponse
):
    print("Recommended destinations:", msg.destinations)
    curr = input("Enter your current location: ")
    dest = input("Enter the Destination Location's airport ID: ")
    query = FlightQuery(current_location=curr, destination_choice=dest)
    await ctx.send(travel_agent_address, query)


@user_agent.on_message(model=FlightResponse, replies={HotelQuery})
async def handle_flight_response(ctx: Context, sender: str, msg: FlightResponse):
    print("Flight price:", msg.lowest_price)
    destiny = input("Enter your destination: ")
    check_in = "2024-03-26"
    check_out = "2024-03-27"
    queryy = HotelQuery(query=destiny, check_in_date=check_in, check_out_date=check_out)
    await ctx.send(travel_agent_address, queryy)


@user_agent.on_message(HotelResponse)
async def handle_hotel_response(ctx: Context, sender: str, msg: HotelResponse):
    print("Hotel Response:", msg.names, msg.links, msg.emails, msg.rates)


if __name__ == "__main__":
    user_agent.run()
