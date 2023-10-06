"""Testing platform"""
from src.uagents import Agent, Bureau, Context
from src.uagents.models import ErrorMessage
from src.uagents.setup import fund_agent_if_low
import dialogue_example as de

agent1 = Agent(name="agent1", seed="9876543210000000000")
agent1._logger.setLevel("DEBUG")
fund_agent_if_low(agent1.wallet.address())

agent2 = Agent(name="agent2", seed="9876543210000000001")
agent2._logger.setLevel("DEBUG")
fund_agent_if_low(agent2.wallet.address())


@agent1.on_message(ErrorMessage)
async def handle_error1(ctx: Context, sender: str, msg: ErrorMessage):
    ctx.logger.error(f"Error received from {sender[-6:]}: {msg.error}")


@agent2.on_message(ErrorMessage)
async def handle_error2(ctx: Context, sender: str, msg: ErrorMessage):
    ctx.logger.error(f"Error received from {sender[-6:]}: {msg.error}")


simple_dialogue1 = de.ResourceRequestDialogue(
    version="0.1",
    agent_address=agent1.address,
)

simple_dialogue2 = de.ResourceRequestDialogue(
    version="0.1",
    agent_address=agent2.address,
)


@simple_dialogue1.on_message(de.ResourceQuery, de.ResourceAvailability)
async def handle_resource_query(
    ctx: Context,
    sender: str,
    _msg: de.ResourceQuery,
):
    ctx.logger.info(f"Resource query received by {sender[-6:]}, session: {ctx.session}")
    await ctx.send(sender, de.ResourceAvailability(qty=1))


@simple_dialogue1.on_message(
    de.ResourceAvailability, {de.ResourceReservation, de.ResourceRejection}
)
async def handle_resource_availability(
    ctx: Context, sender: str, msg: de.ResourceAvailability
):
    ctx.logger.info(f"Received availability, try reservation, session: {ctx.session}")
    if msg.qty == 0:
        await ctx.send(sender, de.ResourceRejection())
        return
    await ctx.send(sender, de.ResourceReservation(qty=1))


@simple_dialogue1.on_message(
    de.ResourceReservation,
    de.ResourceReservationConfirmation,
)
async def handle_resource_reservation(
    ctx: Context, sender: str, _msg: de.ResourceReservation
):
    ctx.logger.info(f"Received reservation, session: {ctx.session}")
    await ctx.send(sender, de.ResourceReservationConfirmation())


@simple_dialogue1.on_message(de.ResourceRejection)
async def handle_resource_rejection(
    ctx: Context,
    _sender: str,
    _msg: de.ResourceRejection,
):
    ctx.logger.info(f"rejected offer, session: {ctx.session}")


@simple_dialogue1.on_message(de.ResourceReservationConfirmation)
async def handle_resource_reservation_confirmation(
    ctx: Context, _sender: str, _msg: de.ResourceReservationConfirmation
):
    ctx.logger.info(f"Confirm reservation, session: {ctx.session}")
    print("---")


@simple_dialogue2.on_message(de.ResourceQuery, de.ResourceAvailability)
async def handle_resource_query2(
    ctx: Context,
    sender: str,
    _msg: de.ResourceQuery,
):
    ctx.logger.info(f"Resource query received by {sender[-6:]}, session: {ctx.session}")
    await ctx.send(sender, de.ResourceAvailability(qty=1))


@simple_dialogue2.on_message(
    de.ResourceAvailability, {de.ResourceReservation, de.ResourceRejection}
)
async def handle_resource_availability2(
    ctx: Context, sender: str, msg: de.ResourceAvailability
):
    ctx.logger.info(f"Received availability, try reservation, session: {ctx.session}")
    if msg.qty == 0:
        await ctx.send(sender, de.ResourceRejection())
        return
    await ctx.send(sender, de.ResourceReservation(qty=1))


@simple_dialogue2.on_message(
    de.ResourceReservation,
    de.ResourceReservationConfirmation,
)
async def handle_resource_reservation2(
    ctx: Context, sender: str, _msg: de.ResourceReservation
):
    ctx.logger.info(f"Received reservation, session: {ctx.session}")
    await ctx.send(sender, de.ResourceReservationConfirmation())


@simple_dialogue2.on_message(de.ResourceRejection)
async def handle_resource_rejection2(
    ctx: Context,
    _sender: str,
    _msg: de.ResourceRejection,
):
    ctx.logger.info(f"offer was rejected, session: {ctx.session}")


@simple_dialogue2.on_message(de.ResourceReservationConfirmation)
async def handle_resource_reservation_confirmation2(
    ctx: Context, _sender: str, _msg: de.ResourceReservationConfirmation
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
        await ctx.send(agent2.address, de.ResourceQuery())
    if counter == 2:
        await ctx.send(agent2.address, de.ResourceRejection())
    counter += 1


if __name__ == "__main__":
    # TODO: do without bureau to have separate states
    bureau = Bureau(port=8080, endpoint="http://localhost:8080/submit")
    bureau.add(agent1)
    print("Agent 1:", agent1.address)
    bureau.add(agent2)
    print("Agent 2:", agent2.address)
    bureau.run()
