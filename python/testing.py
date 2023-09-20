"""Testing platform"""
import uuid
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
}  # all models need to be in the .keys()

simple_dialogue = dialogue.Dialogue(
    dialogue_id=uuid.uuid4(),
    rules=RULES,
)

# --------------


class MessageRequest(Model):
    pass


class MessageResponse(Model):
    text: str


@agent1.on_interval(5)
async def send_message(ctx: Context):
    ctx.logger.info(f"starting session (on_interval): {ctx.session}")
    await ctx.send(agent2.address, MessageRequest())


@agent2.on_message(MessageRequest)
async def handle_message(ctx: Context, sender: str, _msg: MessageRequest):
    ctx.logger.info(f"received session (on_message): {ctx.session}")
    await ctx.send(sender, MessageResponse(text="hello"))


@agent1.on_message(MessageResponse)
async def handle_response(ctx: Context, sender: str, msg: MessageResponse):
    ctx.logger.info(f"received session (on_message): {ctx.session}")
    ctx.logger.info(f"Received response from {sender}: {msg.text}")


bureau = Bureau(port=8080, endpoint="http://localhost:8080/submit")
bureau.add(agent1)
bureau.add(agent2)
bureau.run()
