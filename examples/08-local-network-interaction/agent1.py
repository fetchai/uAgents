from uagents.setup import fund_agent_if_low
from uagents.resolver import get_agent_address
from uagents import Agent, Context, Model


# NOTE: Run agent1.py before running agent2.py


class Message(Model):
    message: str


bob = Agent(
    name="agent bob",
    port=8001,
    seed="agent bob secret phrase",
    endpoint=["http://127.0.0.1:8001/submit"],
)

fund_agent_if_low(bob.wallet.address())
print(bob.address)


@bob.on_event("startup")
async def register_name(ctx: Context):
    await bob.register_name()
    print("agent bob registered address: ", get_agent_address(ctx.name))


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="Hello there alice."))


if __name__ == "__main__":
    bob.run()
