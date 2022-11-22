from typing import List

from nexus import Context, Model, Protocol


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


query_proto = Protocol()


@query_proto.on_message(model=QueryTableRequest, replies={QueryTableResponse})
async def handle_query_request(ctx: Context, sender: str, msg: QueryTableRequest):
    tables = {int(num): TableStatus(**status) for (num, status) in ctx.storage._data.items()}
    
    available_tables = []
    for (number, status) in tables.items():
        if (status.seats >= msg.guests and
            status.time_start <= msg.time_start and
            status.time_end >= msg.time_start + msg.duration):
            available_tables.append(int(number))

    print(f"Query: {msg}. Available tables: {available_tables}.")

    await ctx.send(sender, QueryTableResponse(tables=available_tables))
