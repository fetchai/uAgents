from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class Message(Model):
    message: str


API_KEY = "my_api_key"
MAILBOX_URL = "ws://127.0.0.1:8000"


agent = Agent(
    name="bob",
    seed="bob new phrase",
    mailbox=f"{API_KEY}@{MAILBOX_URL}",
)

fund_agent_if_low(agent.wallet.address())


@agent.on_message(model=Message, replies={Message})
async def bob_rx_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="hello there alice"))


if __name__ == "__main__":
    agent.run()
