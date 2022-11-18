from protocols.book import BookTableRequest, BookTableResponse
from protocols.query import (
    QueryTableRequest,
    QueryTableResponse,
)

from nexus import Agent, Context
from nexus.setup import fund_agent_if_low


RESTAURANT_ADDRESS = "agent1qwkes2mh336psu33f526r4tv9c2wrfl075xme73qs7uv5lyxmsf8ymt0ce5"

user = Agent(
    name="user",
    port=8000,
    seed="agent1 secret phrasexx",
    endpoint="http://127.0.0.1:8000/submit",
)

fund_agent_if_low(user.wallet.address())

table_query = QueryTableRequest(
    guests=3,
    time_start=19,
    duration=2,
)

@user.on_interval(period=3.0)
async def interval(ctx: Context):
    started = ctx.storage.get("started")

    if not started:
        await ctx.send(RESTAURANT_ADDRESS, table_query)

    ctx.storage.set("started", True)


@user.on_message(QueryTableResponse, replies={BookTableRequest})
async def handle_query_response(ctx: Context, sender: str, msg: QueryTableResponse):
    if len(msg.tables) > 0:
        print("There is a free table, attempting to book one now")
        table_number = msg.tables[0]
        request = BookTableRequest(
            table_number=table_number,
            time_start=table_query.time_start,
            duration=table_query.duration
        )
        await ctx.send(sender, request)
    else:
        print("No free tables - nothing more to do")


@user.on_message(BookTableResponse, replies=set())
async def handle_book_response(_ctx: Context, _sender: str, msg: BookTableResponse):
    if msg.success:
        print("Table reservation was successful")
    else:
        print("Table reservation was UNSUCCESSFUL")


if __name__ == "__main__":
    user.run()
