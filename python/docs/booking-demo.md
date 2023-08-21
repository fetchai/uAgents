# Restaurant Booking Demo

To showcase how easy it is to create μAgents for a particular application, here is an example of how to create a custom message type using the `Model` class.

```python
from uagents import Model

class TableStatus(Model):
    seats: int
    time_start: int
    time_end: int
```

For this example, we will create a restaurant booking service with two agents: a `restaurant` with tables available and a `user` requesting table availability.

## Restaurant Setup

We can create a restaurant agent with its corresponding http endpoint. We will also make sure that the agent is funded so it is able to register in the Almanac contract.


```python
from uagents import Agent
from uagents.setup import fund_agent_if_low


restaurant = Agent(
    name="restaurant",
    port=8001,
    seed="restaurant secret phrase",
    endpoint=["http://127.0.0.1:8001/submit"],
)

fund_agent_if_low(restaurant.wallet.address())
```
The protocols `query_proto` and `book_proto` are built from message handlers in the same way as agents. See [query protocol](https://github.com/fetchai/uAgents/blob/main/python/examples/09-booking-protocol-demo/protocols/query.py) and [book protocol](https://github.com/fetchai/uAgents/blob/main/python/examples/09-booking-protocol-demo/protocols/book.py) for the details and logic behind these protocols, but for now we will simply import them. You will need to add these files inside a `protocols` folder in the same directory you are running your agent. See [agent protocols](agent-protocols.md) for more information.
Next we build the restaurant agent from these protocols and set the table availability information.

```python
from protocols.book import book_proto
from protocols.query import query_proto, TableStatus

# build the restaurant agent from stock protocols
restaurant.include(query_proto)
restaurant.include(book_proto)

TABLES = {
    1: TableStatus(seats=2, time_start=16, time_end=22),
    2: TableStatus(seats=4, time_start=19, time_end=21),
    3: TableStatus(seats=4, time_start=17, time_end=19),
}

```

### Storage

We will now store the `TABLES` information in the restaurant agent and run it.

```python
# set the table availability information in the restaurant protocols
for (number, status) in TABLES.items():
    restaurant._storage.set(number, status.dict())

if __name__ == "__main__":
    restaurant.run()
```
The restaurant agent is now online and listing for messages.

## User Setup

We will first import the needed objects and protocols. We will also need the restaurant agent's address to be able to communicate with it.

```python
from protocols.book import BookTableRequest, BookTableResponse
from protocols.query import (
    QueryTableRequest,
    QueryTableResponse,
)

from uagents import Agent, Context
from uagents.setup import fund_agent_if_low


RESTAURANT_ADDRESS = "agent1qw50wcs4nd723ya9j8mwxglnhs2kzzhh0et0yl34vr75hualsyqvqdzl990"

user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint=["http://127.0.0.1:8000/submit"],
)

fund_agent_if_low(user.wallet.address())

```

Now we create the table query to generate the `QueryTableRequest` using the restaurant address. If the request has not been completed before, we send the request to the restaurant agent.

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

The function below activates when a message is received back from the restaurant agent.
`handle_query_response` will evaluate if there is a table available, and if so, respond with a `BookTableRequest` to complete the reservation.

```python
@user.on_message(QueryTableResponse, replies={BookTableRequest})
async def handle_query_response(ctx: Context, sender: str, msg: QueryTableResponse):
    if len(msg.tables) > 0:
        ctx.logger.info("There is a free table, attempting to book one now")
        table_number = msg.tables[0]
        request = BookTableRequest(
            table_number=table_number,
            time_start=table_query.time_start,
            duration=table_query.duration,
        )
        await ctx.send(sender, request)
    else:
        ctx.logger.info("No free tables - nothing more to do")
        ctx.storage.set("completed", True)

```

Then, `handle_book_response` will handle messages from the restaurant agent on whether the reservation was successful or unsuccessful.

```python
@user.on_message(BookTableResponse, replies=set())
async def handle_book_response(ctx: Context, _sender: str, msg: BookTableResponse):
    if msg.success:
        ctx.logger.info("Table reservation was successful")
    else:
        ctx.logger.info("Table reservation was UNSUCCESSFUL")

    ctx.storage.set("completed", True)


if __name__ == "__main__":
    user.run()
```

Finally, run the restaurant agent and then the user agent from different terminals.

!!! example "Run restaurant agent from one terminal"
    
    ``` bash
    python restaurant.py
    ```

!!! example "Run user agent from a second terminal"
    
    ``` bash
    python user.py
    ```

You should see this printed on the user terminal:

<div id="termynal1" data-termynal data-ty-typeDelay="100" data-ty-lineDelay="700">
<span data-ty>INFO:root:Adding funds to agent...complete</span>
<span data-ty>INFO:root:Registering Agent user...</span>
<span data-ty>INFO:root:Registering Agent user...complete.</span>
<span data-ty>Wallet address: fetchnfu3hd87323mw484ma3v3nz2v0q6uhds7d</span>
<span data-ty>There is a free table, attempting to book one now</span>
<span data-ty>Table reservation was successful</span>
</div>

See the full example scripts at [restaurant](https://github.com/fetchai/uAgents/blob/main/python/examples/09-booking-protocol-demo/restaurant.py) and 
[user](https://github.com/fetchai/uAgents/blob/main/python/examples/09-booking-protocol-demo/user.py).
