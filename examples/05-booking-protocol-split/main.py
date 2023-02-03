from protocols.book import BookTableRequest, BookTableResponse, book_proto
from protocols.query import (
    QueryTableRequest,
    QueryTableResponse,
    TableStatus,
    query_proto,
)

from uagents import Agent, Bureau, Context

# build the restaurant agent from stock protocols
restaurant = Agent(name="restaurant")
restaurant.include(query_proto)
restaurant.include(book_proto)

user = Agent(name="user")


@user.on_interval(period=3.0, messages=QueryTableRequest)
async def interval(ctx: Context):
    started = ctx.storage.get("started")

    if not started:
        await ctx.send(restaurant.address, QueryTableRequest(table_number=42))

    ctx.storage.set("started", True)


@user.on_message(QueryTableResponse, replies={BookTableRequest})
async def handle_query_response(ctx: Context, sender: str, msg: QueryTableResponse):
    if msg.status == TableStatus.FREE:
        ctx.logger.info("Table is free, attempting to book it now")
        await ctx.send(sender, BookTableRequest(table_number=42))
    else:
        ctx.logger.info("Table is not free - nothing more to do")


@user.on_message(BookTableResponse, replies=set())
async def handle_book_response(ctx: Context, _sender: str, msg: BookTableResponse):
    if msg.success:
        ctx.logger.info("Table reservation was successful")
    else:
        ctx.logger.info("Table reservation was UNSUCCESSFUL")


# since we have multiple agents in this example we add them to a bureau
# (just an "office" for agents)
bureau = Bureau()
bureau.add(user)
bureau.add(restaurant)


if __name__ == "__main__":
    bureau.run()
