from uagents import Agent, Bureau, Context

alice = Agent(name="alice")
bob = Agent(name="bob")


@alice.on_interval(period=2.0)
async def introduce_alice(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {alice.name}.")


@bob.on_interval(period=2.0)
async def introduce_bob(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {bob.name}.")


bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
