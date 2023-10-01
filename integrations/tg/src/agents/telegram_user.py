from uagents import Agent, Context, Protocol  # Import necessary modules
from messages.basic import TelegramRequest
from uagents.setup import fund_agent_if_low

INPUT_TEXT = "This is a test message for telegram sent by fetch agent."
AI_MODEL_AGENT_ADDRESS = "agent1qdesxanj9s5l9xk4f6nsqqp2k93l7un859s0q3mrcwftxpe60xjg5crcf38"

user_agent = Agent(
    name="telegram_user",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

fund_agent_if_low(user_agent.wallet.address())

user_agent_protocol = Protocol("Request")


@user_agent_protocol.on_interval(360, messages=TelegramRequest)
async def text_classification(ctx: Context):
    ctx.logger.info(f"Asking AI model agent to classify: {INPUT_TEXT}")
    await ctx.send(AI_MODEL_AGENT_ADDRESS, TelegramRequest(text=INPUT_TEXT, chat_id=2032178797))

user_agent.include(user_agent_protocol)

if __name__ == "__main__":
    user_agent_protocol.run()
