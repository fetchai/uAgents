from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model


# NOTE: Run agent1.py before running agent2.py


class Message(Model):
    message: str


bob = Agent(
    name="bob123",
    port=8001,
    seed="bobs secret",
    endpoint=["http://127.0.0.1:8001/submit"],
)

fund_agent_if_low(bob.wallet.address())


@bob.on_event("startup")
async def register_name(ctx: Context):
    await bob.register_name()

print(bob.get_agent_address("hollaaaa"))


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="Hello there alice."))


if __name__ == "__main__":
    bob.run()
