from nexus.setup import fund_agent_if_low
from nexus import Agent, Context, Model


class Message(Model):
    message: str


agent = Agent(
    name="bob",
    port=8001,
    seed="agent2 recovery phrase",
    endpoint=[
        "http://127.0.0.1:8001/submit",
        "http://127.0.0.1:8001/submit",
        "http://127.0.0.1:8001/submit",
    ],
    weight=[2, 4, 6],
)

fund_agent_if_low(agent.wallet.address())


@agent.on_message(model=Message)
async def bob_rx_message(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="hello there alice"))


if __name__ == "__main__":
    agent.run()
