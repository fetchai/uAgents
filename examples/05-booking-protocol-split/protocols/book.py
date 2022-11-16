from nexus import Context, Model, Protocol


class BookTableRequest(Model):
    table_number: int


class BookTableResponse(Model):
    success: bool


book_proto = Protocol()


@book_proto.on_message(model=BookTableRequest)
async def handle_book_request(ctx: Context, sender: str, msg: BookTableRequest):
    if ctx.storage.has(str(msg.table_number)):
        success = False
    else:
        success = True
        ctx.storage.set(str(msg.table_number), sender)

    # send the response
    await ctx.send(sender, BookTableResponse(success=success))
