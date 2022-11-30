from protocols.book import BookTableRequest, BookTableResponse, book_proto
from protocols.query import (
    QueryTableRequest,
    QueryTableResponse,
    TableStatus,
    query_proto,
)

from nexus import Agent, Bureau, Context

# build the restuarant agent from stock protocols
restuarant = Agent(name="restuarant")
restuarant.include(query_proto)
restuarant.include(book_proto)

user = Agent(name="user")


@user.on_interval(period=3.0, messages=QueryTableRequest)
async def interval(ctx: Context):
    started = ctx.storage.get("started")

    if not started:
        await ctx.send(restuarant.address, QueryTableRequest(table_number=42))

    ctx.storage.set("started", True)


@user.on_message(QueryTableResponse, replies={BookTableRequest})
async def handle_query_response(ctx: Context, sender: str, msg: QueryTableResponse):
    if msg.status == TableStatus.FREE:
        print("Table is free, attempting to book it now")
        await ctx.send(sender, BookTableRequest(table_number=42))
    else:
        print("Table is not free - nothing more to do")


@user.on_message(BookTableResponse, replies=set())
async def handle_book_response(_ctx: Context, _sender: str, msg: BookTableResponse):
    if msg.success:
        print("Table reservation was successful")
    else:
        print("Table reservation was UNSUCCESSFUL")


# since we have multiple agents in this example we add them to a bureau
# (just an "office" for agents)
bureau = Bureau()
bureau.add(user)
bureau.add(restuarant)


if __name__ == "__main__":
    bureau.run()
