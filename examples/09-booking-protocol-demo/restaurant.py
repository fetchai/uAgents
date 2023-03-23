from protocols.book import book_proto
from protocols.query import query_proto, TableStatus

from uagents import Agent
from uagents.setup import fund_agent_if_low


restaurant = Agent(
    name="restaurant",
    port=8001,
    seed="restaurant recovery phrase",
    endpoint={
        "http://127.0.0.1:8001/submit": {},
    },
)

fund_agent_if_low(restaurant.wallet.address())

# build the restaurant agent from stock protocols
restaurant.include(query_proto)
restaurant.include(book_proto)

TABLES = {
    1: TableStatus(seats=2, time_start=16, time_end=22),
    2: TableStatus(seats=4, time_start=19, time_end=21),
    3: TableStatus(seats=4, time_start=17, time_end=19),
}

for number, status in TABLES.items():
    restaurant.storage.set(number, status.dict())

if __name__ == "__main__":
    restaurant.run()
