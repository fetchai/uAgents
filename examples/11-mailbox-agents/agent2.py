from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low, register_agent_with_mailbox


class Message(Model):
    message: str


agent = Agent(
    name="bob",
    seed="bob secret phrase",
    mailbox="my_api_key@ws://127.0.0.1:8000",
)

fund_agent_if_low(agent.wallet.address())
register_agent_with_mailbox(agent, "bob@uagent.ai")


@agent.on_message(model=Message, replies={Message})
async def bob_rx_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="hello there alice"))


if __name__ == "__main__":
    agent.run()
