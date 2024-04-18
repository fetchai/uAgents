from uagents import Agent, Context

AGENT_SEED = "put_agents_seed_phrase_here"

WALLET_ADDRESS = "put_your_FETCH_WALLET_ADDRESS_here"

agent = Agent(
    name="alert agent",
    seed=AGENT_SEED,
    enable_wallet_messaging=True,
)


@agent.on_interval(period=5)
async def send_message(ctx: Context):
    msg = "Bitcoin price is too low!"
    ctx.logger.info(f"Sending message to wallet {WALLET_ADDRESS}")
    await ctx.send_wallet_message(WALLET_ADDRESS, msg)


if __name__ == "__main__":
    agent.run()
