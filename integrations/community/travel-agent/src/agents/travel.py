from uagents import Agent
from protocols.flight import flight_proto
from protocols.hotel import hotel_proto
from protocols.destination import query_proto

travel = Agent(
    name="travel",
    port=8001,
    seed="restaurant secret phrase",
    endpoint=["http://127.0.0.1:8001/submit"],
)
# print(travel.address)
travel.include(flight_proto)
travel.include(hotel_proto)
travel.include(query_proto)


if __name__ == "__main__":
    travel.run()
