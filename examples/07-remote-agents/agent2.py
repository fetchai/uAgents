from nexus import Agent, Context, Model
from nexus.resolver import RulesBasedResolver


class Message(Model):
    message: str


AGENT1_ADDRESS = "agent1qwpdqyxwdxmx9ar8gmp02x7n85pjucams0q0m2l45zlmykrzvnpnj5l06gf"
AGENT2_ADDRESS = "agent1q2sec3utj4a8xl8le8x2dy90f33fnlunaatxamjpepz0zk99qqttj97526g"

agent = Agent(
    name="bob",
    port=8001,
    seed="agent2 secret phrase",
    resolve=RulesBasedResolver(
        {
            AGENT1_ADDRESS: "http://127.0.0.1:8000/submit",
            AGENT2_ADDRESS: "http://127.0.0.1:8001/submit",
        }
    ),
)


@agent.on_message(model=Message)
async def bob_rx_message(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")

    # send the response
    await ctx.send(sender, Message(message="hello there alice"))


if __name__ == "__main__":
    agent.run()
