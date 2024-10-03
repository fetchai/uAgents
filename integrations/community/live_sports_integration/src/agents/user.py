# Importing necessary libraries from uagents package
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from message.model import Message, Response


# Specifying the address of the sports agent
Sports_agent = "agent1q034g5mjap6zsex7rvfamuymd2xzggd4xemjrar6jzfy3mknp9sh5qdnvtp"  # replace with your sports agent address

# Defining the user agent with specific configuration details
user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint=["http://localhost:8000/submit"],
)

# Checking and funding the user agent's wallet if its balance is low
fund_agent_if_low(user.wallet.address())


# Event handler for the user agent's startup event
@user.on_interval(period=30.0)
async def agent_address(ctx: Context):
    # Logging the user agent's address
    ctx.logger.info(user.address)
    # Prompting for user input and sending it as a message to the restaurant agent
    sport = str(
        input(
            "Enter the sport name (Football, Tennis, Hockey, Basketball, Volleyball, Handball, Cricket): "
        )
    )
    await ctx.send(Sports_agent, Message(message=sport))


@user.on_message(model=Response)
async def handle_response(ctx: Context, sender: str, msg: Response):
    ctx.logger.info(msg.response)
