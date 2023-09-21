"""Testing platform"""
from src.uagents import Agent, Bureau, Context, Model
from src.uagents.setup import fund_agent_if_low
from src.uagents.contrib.dialogues import dialogue

agent1 = Agent(name="test1", seed="9876543210000000000")

agent2 = Agent(name="test2", seed="9876543210000000001")

fund_agent_if_low(agent1.wallet.address())
fund_agent_if_low(agent2.wallet.address())


class ResourceQuery(Model):
    pass


class ResourceAvailability(Model):
    qty: int


class ResourceRejection(Model):
    pass


class ResourceReservation(Model):
    qty: int


class ResourceReservationConfirmation(Model):
    pass


RULES = {
    ResourceQuery: [ResourceAvailability],
    ResourceAvailability: [ResourceReservation, ResourceRejection],
    ResourceReservation: [ResourceReservationConfirmation],
    ResourceRejection: [],
    ResourceReservationConfirmation: [],
}

simple_dialogue = dialogue.Dialogue(
    rules=RULES,
    starter=ResourceQuery,
    ender={ResourceRejection, ResourceReservationConfirmation},
)


@simple_dialogue.on_message(ResourceQuery, ResourceAvailability)
async def handle_resource_query(
    ctx: Context,
    sender: str,
    _msg: ResourceQuery,
):
    ctx.logger.info(f"starting dialogue, session: {ctx.session}")
    await ctx.send(sender, ResourceAvailability(qty=1))


@simple_dialogue.on_message(
    ResourceAvailability, {ResourceReservation, ResourceRejection}
)
async def handle_resource_availability(
    ctx: Context, sender: str, msg: ResourceAvailability
):
    ctx.logger.info(f"sending response, session: {ctx.session}")
    if msg.qty == 0:
        await ctx.send(sender, ResourceRejection())
    await ctx.send(sender, ResourceReservation(qty=1))


@simple_dialogue.on_message(
    ResourceReservation,
    ResourceReservationConfirmation,
)
async def handle_resource_reservation(
    ctx: Context, sender: str, msg: ResourceReservation
):
    ctx.logger.info(f"received reservation, session: {ctx.session}")
    await ctx.send(sender, ResourceReservationConfirmation())


@simple_dialogue.on_message(ResourceRejection)
async def handle_resource_rejection(
    ctx: Context,
    _sender: str,
    msg: ResourceRejection,
):
    ctx.logger.info(f"rejected offer, cleanup of session: {ctx.session}")


@simple_dialogue.on_message(ResourceReservationConfirmation)
async def handle_resource_reservation_confirmation(
    ctx: Context, sender: str, msg: ResourceReservationConfirmation
):
    ctx.logger.info(f"dialogue finished, cleanup of session: {ctx.session}")


agent1.include(simple_dialogue)
print()

# --------------


# class MessageRequest(Model):
#     pass


# class MessageResponse(Model):
#     text: str


# @agent1.on_interval(5)
# async def send_message(ctx: Context):
#     ctx.logger.info(f"starting session (on_interval): {ctx.session}")
#     await ctx.send(agent2.address, MessageRequest())


# @agent2.on_message(MessageRequest)
# async def handle_message(ctx: Context, sender: str, _msg: MessageRequest):
#     ctx.logger.info(f"received session (on_message): {ctx.session}")
#     await ctx.send(sender, MessageResponse(text="hello"))


# @agent1.on_message(MessageResponse)
# async def handle_response(ctx: Context, sender: str, msg: MessageResponse):
#     ctx.logger.info(f"received session (on_message): {ctx.session}")
#     ctx.logger.info(f"Received response from {sender}: {msg.text}")


bureau = Bureau(port=8080, endpoint="http://localhost:8080/submit")
bureau.add(agent1)
bureau.add(agent2)
bureau.run()
