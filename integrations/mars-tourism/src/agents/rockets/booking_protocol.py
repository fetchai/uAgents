# Import necessary modules and classes from external libraries
from ai_engine import UAgentResponse, UAgentResponseType, BookingRequest
from uagents import Context, Protocol

# Define a function to create a booking protocol
def booking_proto():
    # Create a new protocol instance
    protocol = Protocol("BookingProtocol")

    # Define behavior when receiving a booking request message
    @protocol.on_message(model=BookingRequest, replies={UAgentResponse})
    async def booking_handler(ctx: Context, sender: str, msg: BookingRequest):
        # Log the booking request
        ctx.logger.info(f"Received booking request from {sender}")
        try:
            # Retrieve the options from context storage using the request ID
            option = ctx.storage.get(msg.request_id)
            # Store the chosen option in context storage
            ctx.storage.set("choosen_options", option[msg.user_response])
            # Send a response acknowledging the chosen option
            await ctx.send(
                sender,
                UAgentResponse(
                    message=f"Thanks for choosing an option - {option[msg.user_response]}.",
                    type=UAgentResponseType.FINAL,
                    request_id=msg.request_id
                )
            )
        except Exception as exc:
            # Handle any exceptions and send an error response
            ctx.logger.error(exc)
            await ctx.send(
                sender,
                UAgentResponse(
                    message=str(exc),
                    type=UAgentResponseType.ERROR
                )
            )

    return protocol  # Return the created protocol
