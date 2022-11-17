from enum import Enum

from nexus import Agent, Bureau, Context, Model


class TableStatus(str, Enum):
    RESERVED = "reserved"
    FREE = "free"


class QueryTableRequest(Model):
    table_number: int


class QueryTableResponse(Model):
    status: TableStatus


class BookTableRequest(Model):
    table_number: int


class BookTableResponse(Model):
    success: bool


user = Agent(name="user")
restuarant = Agent(name="restuarant")


@user.on_interval(period=3.0)
async def interval(ctx: Context):
    started = ctx.storage.get("started")

    if not started:
        await ctx.send(restuarant.address, QueryTableRequest(table_number=42))

    ctx.storage.set("started", True)


@user.on_message(QueryTableResponse, replies={BookTableRequest})
async def handle_query_response(ctx: Context, _sender: str, msg: QueryTableResponse):
    if msg.status == TableStatus.FREE:
        print("Table is free, attempting to book it now")
        await ctx.send(restuarant.address, BookTableRequest(table_number=42))
    else:
        print("Table is not free - nothing more to do")


@user.on_message(BookTableResponse, replies={})
async def handle_book_response(_ctx: Context, _sender: str, msg: BookTableResponse):
    if msg.success:
        print("Table reservation was successful")
    else:
        print("Table reservation was UNSUCCESSFUL")


@restuarant.on_message(model=QueryTableRequest, replies={QueryTableResponse})
async def handle_query_request(ctx: Context, sender: str, msg: QueryTableRequest):
    if ctx.storage.has(str(msg.table_number)):
        status = TableStatus.RESERVED
    else:
        status = TableStatus.FREE

    print(f"Table {msg.table_number} query. Status: {status}")

    await ctx.send(sender, QueryTableResponse(status=status))


@restuarant.on_message(model=BookTableRequest, replies={BookTableResponse})
async def handle_book_request(ctx: Context, sender: str, msg: BookTableRequest):
    if ctx.storage.has(str(msg.table_number)):
        success = False
    else:
        success = True
        ctx.storage.set(str(msg.table_number), sender)

    # send the response
    await ctx.send(sender, BookTableResponse(success=success))


# since we have multiple agents in this example we add them to a bureau
# (just an "office" for agents)
bureau = Bureau()
bureau.add(user)
bureau.add(restuarant)

if __name__ == "__main__":
    bureau.run()
