from uagents import Agent, Bureau, Context
from uagents.wallet_messaging import WalletMessage


alice_seed = "alice recovery phrase"
bob_seed = "bob recovery phrase"

alice = Agent(name="alice", seed=alice_seed, enable_wallet_messaging=True)
bob = Agent(name="bob", seed=bob_seed, enable_wallet_messaging=True)


@alice.on_wallet_message()
async def reply(ctx: Context, msg: WalletMessage):
    ctx.logger.info(f"Got wallet message: {msg.text}")
    await ctx.send_wallet_message(msg.sender, "hey, thanks for the message")


@bob.on_interval(period=5)
async def send_message(ctx: Context):
    ctx.logger.info("Sending message...")
    await ctx.send_wallet_message(alice.address, "hello")


@bob.on_wallet_message()
async def reply(ctx: Context, msg: WalletMessage):
    ctx.logger.info(f"Got wallet message: {msg.text}")


bureau = Bureau()
bureau.add(alice)
bureau.add(bob)
bureau.run()
