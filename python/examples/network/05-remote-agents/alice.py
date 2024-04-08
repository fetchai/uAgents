from pyngrok import conf, ngrok, conf
from uagents import Agent, Context, Model


class Message(Model):
    message: str


PORT = 8000

conf.get_default().monitor_thread = False  # reduce console output
http_tunnel = ngrok.connect(addr=PORT, proto="http", name="remote_agent")

ALICE_SEED = "put_your_seed_phrase_here"

alice = Agent(
    name="alice",
    seed=ALICE_SEED,
    port=PORT,
    endpoint=[f"{http_tunnel.public_url}/submit"],
)


@alice.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender[-8:]}: {msg.message}")


print(f"Agent address: {alice.address}")
print(f"Agent public URL: {http_tunnel.public_url}/submit")

if __name__ == "__main__":
    alice.run()
