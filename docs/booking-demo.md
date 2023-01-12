# Restaurant Booking Demo

## Restaurant Setup

We can create a restaurant agent with its corresponding HTTP endpoint. We will also make sure that the agent is funded so it is able to register in the `contract-almanac`.


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
    restaurant._storage.set(number, status.dict())

if __name__ == "__main__":
    restaurant.run()
```

## User Setup

The restaurant agent will be on hold waiting for a user to request a table, therefore we will need to run a user agent. 
We will first import some libraries and the booking protocols. We will need the restaurant agent's address to be able to communicate with it.


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

Now we create the table query to generate the `QueryTableRequest` using the restaurant address. If the request has not been completed, we send the request to the restaurant agent

```python
table_query = QueryTableRequest(
    guests=3,
    time_start=19,
    duration=2,
)

# This on_interval agent function performs a request on a defined period

@user.on_interval(period=3.0, messages=QueryTableRequest)
async def interval(ctx: Context):
    completed = ctx.storage.get("completed")

    if not completed:
        await ctx.send(RESTAURANT_ADDRESS, table_query)
```

The functions below activate when a message is received back from the restaurant agent.
`handle_query_response` will evaluate if there is a table available, if this is the case, the user
agent will respond with a `BookTableRequest` to make the reservation

```python
@user.on_message(QueryTableResponse, replies={BookTableRequest})
async def handle_query_response(ctx: Context, sender: str, msg: QueryTableResponse):
    if len(msg.tables) > 0:
        print("There is a free table, attempting to book one now")
        table_number = msg.tables[0]
        request = BookTableRequest(
            table_number=table_number,
            time_start=table_query.time_start,
            duration=table_query.duration,
        )
        await ctx.send(sender, request)
    else:
        print("No free tables - nothing more to do")
        ctx.storage.set("completed", True)

```

Finally, `handle_book_response` will receive a message from the restaurant agent saying if the 
reservation was successful or unsuccessful.

```python


@user.on_message(BookTableResponse, replies=set())
async def handle_book_response(ctx: Context, _sender: str, msg: BookTableResponse):
    if msg.success:
        print("Table reservation was successful")
    else:
        print("Table reservation was UNSUCCESSFUL")

    ctx.storage.set("completed", True)


if __name__ == "__main__":
    user.run()
```
