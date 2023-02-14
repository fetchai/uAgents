from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class Message(Model):
    message: str


API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZ2VudEBmZXRjaC5haSIsImV4cCI6MTY3NjMwOTY0Nn0.uZRrJdZoxupWyLsLDjd8oZ8h5x_u0jL9UThftGeImKE"  # pylint: disable=line-too-long

agent = Agent(
    name="bob",
    seed="bob secret phrase",
    mailbox=API_KEY,
)

fund_agent_if_low(agent.wallet.address())


@agent.on_message(model=Message, replies={Message})
async def bob_rx_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="hello there alice"))


if __name__ == "__main__":
    agent.run()
