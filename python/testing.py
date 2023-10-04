"""Testing platform"""
from src.uagents import Agent, Bureau, Context, Model
from src.uagents.contrib.dialogues import dialogue
from src.uagents.models import ErrorMessage
from src.uagents.setup import fund_agent_if_low

agent1 = Agent(name="test1", seed="9876543210000000000")
# agent1._logger.setLevel("DEBUG")
fund_agent_if_low(agent1.wallet.address())

agent2 = Agent(name="test2", seed="9876543210000000001")
# agent2._logger.setLevel("DEBUG")
fund_agent_if_low(agent2.wallet.address())


@agent1.on_message(ErrorMessage)
async def handle_error1(ctx: Context, sender: str, msg: ErrorMessage):
    ctx.logger.error(f"Error received from {sender}: {msg.error}")


@agent2.on_message(ErrorMessage)
async def handle_error2(ctx: Context, sender: str, msg: ErrorMessage):
    ctx.logger.error(f"Error received from {sender}: {msg.error}")


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


# predefine structure and enable passing specific messages into the structure
RULES = {
    ResourceQuery: [ResourceAvailability],
    ResourceAvailability: [ResourceReservation, ResourceRejection],
    ResourceReservation: [ResourceReservationConfirmation],
    ResourceRejection: [],
    ResourceReservationConfirmation: [],
}

simple_dialogue1 = dialogue.Dialogue(
    name="simple_dialogue1",
    version="0.1",
    rules=RULES,
    starter=ResourceQuery,
    ender={ResourceRejection, ResourceReservationConfirmation},
)

simple_dialogue2 = dialogue.Dialogue(
    name="simple_dialogue2",
    version="0.1",
    rules=RULES,
    starter=ResourceQuery,
    ender={ResourceRejection, ResourceReservationConfirmation},
)


@simple_dialogue1.on_message(ResourceQuery, ResourceAvailability)
async def handle_resource_query(
    ctx: Context,
    sender: str,
    _msg: ResourceQuery,
):
    ctx.logger.info(f"Resource query received by {sender[-6:]}, session: {ctx.session}")
    await ctx.send(sender, ResourceAvailability(qty=1))


@simple_dialogue1.on_message(
    ResourceAvailability, {ResourceReservation, ResourceRejection}
)
async def handle_resource_availability(
    ctx: Context, sender: str, msg: ResourceAvailability
):
    ctx.logger.info(f"Received availability, try reservation, session: {ctx.session}")
    if msg.qty == 0:
        await ctx.send(sender, ResourceRejection())
    await ctx.send(sender, ResourceReservation(qty=1))


@simple_dialogue1.on_message(
    ResourceReservation,
    ResourceReservationConfirmation,
)
async def handle_resource_reservation(
    ctx: Context, sender: str, msg: ResourceReservation
):
    ctx.logger.info(f"Received reservation, session: {ctx.session}")
    await ctx.send(sender, ResourceReservationConfirmation())


@simple_dialogue1.on_message(ResourceRejection)
async def handle_resource_rejection(
    ctx: Context,
    _sender: str,
    msg: ResourceRejection,
):
    ctx.logger.info(f"rejected offer, session: {ctx.session}")


@simple_dialogue1.on_message(ResourceReservationConfirmation)
async def handle_resource_reservation_confirmation(
    ctx: Context, sender: str, msg: ResourceReservationConfirmation
):
    ctx.logger.info(f"Confirm reservation, session: {ctx.session}")
    print("---")


@simple_dialogue2.on_message(ResourceQuery, ResourceAvailability)
async def handle_resource_query2(
    ctx: Context,
    sender: str,
    _msg: ResourceQuery,
):
    ctx.logger.info(f"Resource query received by {sender[-6:]}, session: {ctx.session}")
    await ctx.send(sender, ResourceAvailability(qty=1))


@simple_dialogue2.on_message(
    ResourceAvailability, {ResourceReservation, ResourceRejection}
)
async def handle_resource_availability2(
    ctx: Context, sender: str, msg: ResourceAvailability
):
    ctx.logger.info(f"Received availability, try reservation, session: {ctx.session}")
    if msg.qty == 0:
        await ctx.send(sender, ResourceRejection())
    await ctx.send(sender, ResourceReservation(qty=1))


@simple_dialogue2.on_message(
    ResourceReservation,
    ResourceReservationConfirmation,
)
async def handle_resource_reservation2(
    ctx: Context, sender: str, msg: ResourceReservation
):
    ctx.logger.info(f"Received reservation, session: {ctx.session}")
    await ctx.send(sender, ResourceReservationConfirmation())


@simple_dialogue2.on_message(ResourceRejection)
async def handle_resource_rejection2(
    ctx: Context,
    _sender: str,
    msg: ResourceRejection,
):
    ctx.logger.info(f"offer was rejected, session: {ctx.session}")


@simple_dialogue2.on_message(ResourceReservationConfirmation)
async def handle_resource_reservation_confirmation2(
    ctx: Context, sender: str, msg: ResourceReservationConfirmation
):
    ctx.logger.info(f"Confirm reservation, session: {ctx.session}")
    print("---")


agent1.include(simple_dialogue1)
agent2.include(simple_dialogue2)

counter = 0


@agent1.on_interval(5)
async def handle_interval(ctx: Context):
    global counter
    if counter == 1:
        await ctx.send(agent2.address, ResourceQuery())
    if counter == 2:
        await ctx.send(agent2.address, ResourceRejection())
    counter += 1


if __name__ == "__main__":
    # TODO: do without bureau to have separate states
    bureau = Bureau(port=8080, endpoint="http://localhost:8080/submit")
    bureau.add(agent1)
    bureau.add(agent2)
    bureau.run()
