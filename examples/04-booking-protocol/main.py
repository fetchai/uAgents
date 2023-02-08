from enum import Enum

from uagents import Agent, Bureau, Context, Model


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
restaurant = Agent(name="restaurant")


@user.on_interval(period=3.0, messages=QueryTableRequest)
async def interval(ctx: Context):
    started = ctx.storage.get("started")

    if not started:
        await ctx.send(restaurant.address, QueryTableRequest(table_number=42))

    ctx.storage.set("started", True)


@user.on_message(QueryTableResponse, replies=BookTableRequest)
async def handle_query_response(ctx: Context, _sender: str, msg: QueryTableResponse):
    if msg.status == TableStatus.FREE:
        ctx.logger.info("Table is free, attempting to book it now")
        await ctx.send(restaurant.address, BookTableRequest(table_number=42))
    else:
        ctx.logger.info("Table is not free - nothing more to do")


@user.on_message(BookTableResponse, replies=set())
async def handle_book_response(ctx: Context, _sender: str, msg: BookTableResponse):
    if msg.success:
        ctx.logger.info("Table reservation was successful")
    else:
        ctx.logger.info("Table reservation was UNSUCCESSFUL")


@restaurant.on_message(model=QueryTableRequest, replies=QueryTableResponse)
async def handle_query_request(ctx: Context, sender: str, msg: QueryTableRequest):
    if ctx.storage.has(str(msg.table_number)):
        status = TableStatus.RESERVED
    else:
        status = TableStatus.FREE

    ctx.logger.info(f"Table {msg.table_number} query. Status: {status}")

    await ctx.send(sender, QueryTableResponse(status=status))


@restaurant.on_message(model=BookTableRequest, replies=BookTableResponse)
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
bureau.add(restaurant)

if __name__ == "__main__":
    bureau.run()
