from typing import List

from uagents import Context, Model, Protocol


class TableStatus(Model):
    seats: int
    time_start: int
    time_end: int


class QueryTableRequest(Model):
    guests: int
    time_start: int
    duration: int


class QueryTableResponse(Model):
    tables: List[int]


class GetTotalQueries(Model):
    pass


class TotalQueries(Model):
    total_queries: int


query_proto = Protocol(name="RestaurantQueryProtocolExample", version="0.1.0")


@query_proto.on_message(model=QueryTableRequest, replies=QueryTableResponse)
async def handle_query_request(ctx: Context, sender: str, msg: QueryTableRequest):
    tables = {
        int(num): TableStatus(**status)
        for (
            num,
            status,
        ) in ctx.storage._data.items()  # pylint: disable=protected-access
        if isinstance(num, int)
    }

    available_tables = []
    for number, status in tables.items():
        if (
            status.seats >= msg.guests
            and status.time_start <= msg.time_start
            and status.time_end >= msg.time_start + msg.duration
        ):
            available_tables.append(int(number))

    ctx.logger.info(f"Query: {msg}. Available tables: {available_tables}.")

    await ctx.send(sender, QueryTableResponse(tables=available_tables))

    total_queries = int(ctx.storage.get("total_queries") or 0)
    ctx.storage.set("total_queries", total_queries + 1)


@query_proto.on_query(model=GetTotalQueries, replies=TotalQueries)
async def handle_get_total_queries(ctx: Context, sender: str, _msg: GetTotalQueries):
    total_queries = int(ctx.storage.get("total_queries") or 0)
    await ctx.send(sender, TotalQueries(total_queries=total_queries))
