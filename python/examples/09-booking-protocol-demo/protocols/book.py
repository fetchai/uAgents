from uagents import Context, Model, Protocol

from .query import TableStatus


class BookTableRequest(Model):
    table_number: int
    time_start: int
    duration: int


class BookTableResponse(Model):
    success: bool


book_proto = Protocol(name="RestaurantBookingProtocolExample", version="0.1.0")


@book_proto.on_message(model=BookTableRequest, replies=BookTableResponse)
async def handle_book_request(ctx: Context, sender: str, msg: BookTableRequest):
    tables = {
        int(num): TableStatus(**status)
        for (
            num,
            status,
        ) in ctx.storage._data.items()  # pylint: disable=protected-access
        if isinstance(num, int)
    }
    table = tables[msg.table_number]

    if (
        table.time_start <= msg.time_start
        and table.time_end >= msg.time_start + msg.duration
    ):
        success = True
        table.time_start = msg.time_start + msg.duration
        ctx.storage.set(msg.table_number, table.dict())
    else:
        success = False

    # send the response
    await ctx.send(sender, BookTableResponse(success=success))
