from ai_engine import UAgentResponse, UAgentResponseType, BookingRequest


def booking_proto():
    protocol = Protocol("BookingProtocol")

    @protocol.on_message(model=BookingRequest, replies={UAgentResponse})
    async def booking_handler(ctx: Context, sender: str, msg: BookingRequest):
        ctx.logger.info(f"Received booking request from {sender}")
        try:
            option = ctx.storage.get(msg.request_id)
            await ctx.send(
                sender,
                UAgentResponse(
                    message=f"Thanks for choosing an option - {option[msg.user_response]}.",
                    type=UAgentResponseType.FINAL,
                    request_id=msg.request_id
                )
            )
        except Exception as exc:
            ctx.logger.error(exc)
            await ctx.send(
                sender,
                UAgentResponse(
                    message=str(exc),
                    type=UAgentResponseType.ERROR
                )
            )

    return protocol
