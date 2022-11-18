from cosmpy.aerial.client import NetworkConfig
from cosmpy.aerial.faucet import FaucetApi

from protocols.book import BookTableRequest, BookTableResponse, book_proto
from protocols.query import (
    QueryTableRequest,
    QueryTableResponse,
    TableStatus,
    query_proto,
)

from nexus.network import get_ledger
from nexus import Agent, Bureau, Context
from nexus.resolver import AlmanacResolver, RulesBasedResolver

from protocols.book import TableStatus


USER_ADDRESS = "agent1qwe352gculwjd9v9s49ucfy429y0trugte0m5rsla3wnu4kufhm4g2a0npu"


restaurant = Agent(
    name="restaurant",
    port=8001,
    seed="agent2 secret phrasexx",
    endpoint="http://127.0.0.1:8001/submit",
    resolve=AlmanacResolver(),
)

# build the restaurant agent from stock protocols
restaurant.include(query_proto)
restaurant.include(book_proto)

TABLES = {
    1: TableStatus(seats=2, time_start=16, time_end=22),
    2: TableStatus(seats=4, time_start=19, time_end=21),
    3: TableStatus(seats=4, time_start=17, time_end=19),
}

for (number, status) in TABLES.items():
    restaurant._storage.set(number, status.dict())

ledger = get_ledger("fetchai-testnet")
faucet_api = FaucetApi(NetworkConfig.latest_stable_testnet())
restaurant_balance = ledger.query_bank_balance(restaurant.wallet.address())


if restaurant_balance < 500000000000000000:
    # Add tokens to agent's wallet
    faucet_api.get_wealth(restaurant.wallet.address())


if __name__ == "__main__":
    restaurant.run()
