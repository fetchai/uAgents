# Restaurant Booking Demo

## Restaurant Setup

We can create the restaurant agent with its corresponding HTTP endpoint. We will also make sure that the agent is funded so it is able to register in the `contract almanac`.


```python
from protocols.book import book_proto
from protocols.query import query_proto, TableStatus

from nexus import Agent
from nexus.setup import fund_agent_if_low


restaurant = Agent(
    name="restaurant",
    port=8001,
    seed="restaurant secret phrase",
    endpoint="http://127.0.0.1:8001/submit",
)

fund_agent_if_low(restaurant.wallet.address())
```
We now build the restaurant protocols and set the table availability information. Finally, we run the restaurant agent.

```python
# build the restaurant agent from stock protocols
restaurant.include(query_proto)
restaurant.include(book_proto)

TABLES = {
    1: TableStatus(seats=2, time_start=16, time_end=22),
    2: TableStatus(seats=4, time_start=19, time_end=21),
    3: TableStatus(seats=4, time_start=17, time_end=19),
}

# set the table availability information in the restaurant protocols
for (number, status) in TABLES.items():
    restaurant._storage.set(number, status.dict())  # pylint: disable=protected-access

if __name__ == "__main__":
    restaurant.run()
```

The restaurant agent will be on hold waiting for a user to request a table, therefore we will need to run a user agent. 
We will first import some libraries and the booking protocols. We will need the restaurant agent addres to be able to communicate with it.

```python
from protocols.book import BookTableRequest, BookTableResponse
from protocols.query import (
    QueryTableRequest,
    QueryTableResponse,
)

from nexus import Agent, Context
from nexus.setup import fund_agent_if_low


RESTAURANT_ADDRESS = "agent1qw50wcs4nd723ya9j8mwxglnhs2kzzhh0et0yl34vr75hualsyqvqdzl990"

user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint="http://127.0.0.1:8000/submit",
)

fund_agent_if_low(user.wallet.address())

```

Now we create the table query to generate the request.

```python
table_query = QueryTableRequest(
    guests=3,
    time_start=19,
    duration=2,
)
```