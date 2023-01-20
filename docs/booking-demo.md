# Restaurant Booking Demo

uAgents are very flexible and customizable, you can create any type of interaction you can think of by customizing the `Model` class. Below is an example of how to create a costume-made
class using `Model`

```python
from nexus import Model

class TableStatus(Model):
    seats: int
    time_start: int
    time_end: int
```

For this example, we will create a restaurant booking service with two agents: a `restaurant` with tables available and a `user` requesting table availability.

## Restaurant Setup

We can create a restaurant agent with its corresponding http endpoint. We will also make sure that the agent is funded so it is able to register in the `contract-almanac`.


```python
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
These `query_proto` and `book_proto` are more complex message handlers to manage the logic behind the table booking request from the user. You can view them at [query protocol](https://github.com/fetchai/uAgents/blob/master/examples/09-booking-protocol-demo/protocols/query.py) and [book protocol](https://github.com/fetchai/uAgents/blob/master/examples/09-booking-protocol-demo/protocols/book.py).
We now build the restaurant protocols and set the table availability information.

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

You can store information using the agent's storage by simply running:

```python
agent._storage.set("key", "value")
```
This will save the information in a JSON file, you can retreive it a any time using `agent._storage.get("key")`.

We will now store the `TABLES` information in the restaurant agent and run it.

```python
# set the table availability information in the restaurant protocols
for (number, status) in TABLES.items():
    restaurant._storage.set(number, status.dict())

if __name__ == "__main__":
    restaurant.run()
```
The restaurant agent will remain on "hold" until we run the user agent to request a table booking.

## User Setup

We will first make some imports including the needed protocols. We will need the restaurant agent's address to be able to communicate with it.


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

Now we create the table query to generate the `QueryTableRequest`. using the restaurant address. If the request has not been completed before, we send the request to the restaurant agent

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

Then, `handle_book_response` will receive a message from the restaurant agent saying if the 
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

Finally, run the restaurant agent and then the user agent

!!! example "Run Restaurant and User agents"
    
    ``` bash
    python restaurant.py
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

See the full example scripts at [restaurant](https://github.com/fetchai/uAgents/blob/master/examples/09-booking-protocol-demo/restaurant.py) and 
[user](https://github.com/fetchai/uAgents/blob/master/examples/09-booking-protocol-demo/user.py) and check out the protocols for more information on how the booking process 
works.
