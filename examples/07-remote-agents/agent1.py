from nexus.agent import Agent
from nexus.context import Context
from nexus.models import Model
from nexus.resolver import RulesBasedResolver


class Message(Model):
    message: str


AGENT1_ADDRESS = "agent1qwpdqyxwdxmx9ar8gmp02x7n85pjucams0q0m2l45zlmykrzvnpnj5l06gf"
AGENT2_ADDRESS = "agent1q2sec3utj4a8xl8le8x2dy90f33fnlunaatxamjpepz0zk99qqttj97526g"

agent = Agent(
    name="alice",
    port=8000,
    seed="agent1 secret phrase",
    resolve=RulesBasedResolver(
        {
            AGENT1_ADDRESS: "http://127.0.0.1:8000/submit",
            AGENT2_ADDRESS: "http://127.0.0.1:8001/submit",
        }
    ),
)


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(AGENT2_ADDRESS, Message(message="hello there bob"))


@agent.on_message(model=Message)
async def on_message(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")


if __name__ == "__main__":
    agent.run()
