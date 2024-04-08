from uagents import Agent, Bureau, Context
from uagents.wallet_messaging import WalletMessage


ALICE_SEED = "put_alices_seed_phrase_here"
BOB_SEED = "put_bobs_seed_phrase_here"

alice = Agent(name="alice", seed=ALICE_SEED, enable_wallet_messaging=True)
bob = Agent(name="bob", seed=BOB_SEED, enable_wallet_messaging=True)


@alice.on_interval(period=5)
async def send_message(ctx: Context):
    msg = f"Hello there {bob.name}."
    await ctx.send_wallet_message(bob.address, msg)


@bob.on_wallet_message()
async def wallet_message_handler(ctx: Context, msg: WalletMessage):
    ctx.logger.info(f"Received wallet message from {msg.sender}: {msg.text}")
    await ctx.send_wallet_message(msg.sender, f"Hello there {alice.name}.")


@alice.on_wallet_message()
async def wallet_message_handler(ctx: Context, msg: WalletMessage):
    ctx.logger.info(f"Received wallet message from: {msg.sender}: {msg.text}")


bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
