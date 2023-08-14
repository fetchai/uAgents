import hashlib
from uagents import Agent, Bureau, Context, Model
from uagents.crypto import Identity


class Message(Model):
    message: str
    digest: str
    signature: str


def encode(message: str) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(message.encode())
    return hasher.digest()


alice = Agent(name="alice", seed="alice recovery password")
bob = Agent(name="bob", seed="bob recovery password")


@alice.on_interval(period=3.0)
async def send_message(ctx: Context):
    msg = "Hello there bob."
    digest = encode(msg)
    await ctx.send(
        bob.address,
        Message(message=msg, digest=digest.hex(), signature=alice.sign_digest(digest)),
    )


@alice.on_message(model=Message)
async def alice_rx_message(ctx: Context, sender: str, msg: Message):
    assert Identity.verify_digest(
        sender, bytes.fromhex(msg.digest), msg.signature
    ), "couldn't verify bob's message"

    ctx.logger.info("Bob's message verified!")
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


@bob.on_message(model=Message)
async def bob_rx_message(ctx: Context, sender: str, msg: Message):
    assert Identity.verify_digest(
        sender, bytes.fromhex(msg.digest), msg.signature
    ), "couldn't verify alice's message"
    ctx.logger.info("Alice's message verified!")

    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    msg = "Hello there alice."
    digest = encode(msg)

    # send the response
    await ctx.send(
        alice.address,
        Message(message=msg, digest=digest.hex(), signature=bob.sign_digest(digest)),
    )


bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
