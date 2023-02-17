# Agent protocols

When trying to create agent interactions, it might be necessary to add protocols that contain more complex handlers to perform the desired logic within agents.

We first need to define the type of messages that the handler will receive and send. We will use a table book request as an example.
Here we define `BookTableRequest` which will contain the requested table number and `BookTableResponse` which will send back to the user if that table number is available.

```python
from uagents import Context, Model, Protocol


class BookTableRequest(Model):
    table_number: int


class BookTableResponse(Model):
    success: bool

```

Now we define the booking protocol as `book_proto` and we define the desired logic to determine if the `BookTableResponse` will be successful or not.

```python
book_proto = Protocol()


@book_proto.on_message(model=BookTableRequest, replies={BookTableResponse})
async def handle_book_request(ctx: Context, sender: str, msg: BookTableRequest):
    if ctx.storage.has(str(msg.table_number)):
        success = False
    else:
        success = True
        ctx.storage.set(str(msg.table_number), sender)

    # send the response
    await ctx.send(sender, BookTableResponse(success=success))

```

Save this file as `book.py`. To alow your agent to use this protocol, you can simply create a folder called protocols withing the directory you are running your agent from and then import it from your agent's script:

```python
from protocols.book import book_proto
```

Then, if your agent is called `restaurant` you can include the protocol in this way:

```python
restaurant.include(book_proto)
```