from enum import Enum

from uagents import Context, Model, Protocol


class TableStatus(str, Enum):
    RESERVED = "reserved"
    FREE = "free"


class QueryTableRequest(Model):
    table_number: int


class QueryTableResponse(Model):
    status: TableStatus


query_proto = Protocol()


@query_proto.on_message(model=QueryTableRequest, replies={QueryTableResponse})
async def handle_query_request(ctx: Context, sender: str, msg: QueryTableRequest):
    if ctx.storage.has(str(msg.table_number)):
        status = TableStatus.RESERVED
    else:
        status = TableStatus.FREE

    print(f"Table {msg.table_number} query. Status: {status}")

    await ctx.send(sender, QueryTableResponse(status=status))
