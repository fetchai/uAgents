# Importing necessary classes from modules
from ai_engine import UAgentResponse, UAgentResponseType, BookingRequest
from uagents import Protocol, Context

# Function to define a booking protocol
def booking_proto():
    # Creating a protocol object with the name "BookingProtocol"
    protocol = Protocol("BookingProtocol")

    # Defining a message handler for booking requests
    @protocol.on_message(model=BookingRequest, replies={UAgentResponse})
    async def booking_handler(ctx: Context, sender: str, msg: BookingRequest):
        # Logging information about the received booking request
        ctx.logger.info(f"Received booking request from {sender}")

        try:
            # Retrieving option from storage based on the request ID
            option = ctx.storage.get(msg.request_id)
            # Setting the chosen option in storage
            ctx.storage.set("choosen_options", option[msg.user_response])
            # Sending a response to the sender acknowledging the choice
            await ctx.send(
                sender,
                UAgentResponse(
                    message=f"Thanks for choosing an option - {option[msg.user_response]}",
                    type=UAgentResponseType.FINAL,
                    request_id=msg.request_id
                )
            )
        except Exception as exc:
            # Handling any exceptions that occur during the process
            ctx.logger.error(exc)
            # Sending an error response to the sender
            await ctx.send(
                sender,
                UAgentResponse(
                    message=str(exc),
                    type=UAgentResponseType.ERROR
                )
            )

    return protocol
