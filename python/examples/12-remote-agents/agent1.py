"""
Remote connection example which uses ngrok to expose the agent as an
alternative to the Fetch.ai Agentverse. (https://agentverse.ai/)

Preparation:
 - pip install pyngrok
 - during the first run, the script will download the ngrok application
   (no installation or registration required)
"""
from pyngrok import conf, ngrok

from uagents import Agent, Context, Model


class Message(Model):
    message: str


PORT = 8000

conf.get_default().monitor_thread = False  # reduce console output
http_tunnel = ngrok.connect(addr=PORT, proto="http", name="remote_agent")

alice = Agent(
    name="Alice",
    seed="agent1 secret phrase",
    port=PORT,
    endpoint=[f"{http_tunnel.public_url}/submit"],
)


@alice.on_message(model=Message)
async def act_on_message(ctx: Context, sender: str, msg: Message):
    """On message handler"""
    ctx.logger.info(f"Received message from {sender[-8:]}: {msg.message}")


print(f"Agent address: {alice.address}")
print(f"Agent public URL: {http_tunnel.public_url}/submit")

if __name__ == "__main__":
    alice.run()
