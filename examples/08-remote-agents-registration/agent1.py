from cosmpy.aerial.client import NetworkConfig
from cosmpy.aerial.faucet import FaucetApi

from nexus.network import get_ledger
from nexus import Agent, Context, Model
from nexus.resolver import AlmanacResolver


class Message(Model):
    message: str


RECIPIENT_ADDRESS = "agent1q2sec3utj4a8xl8le8x2dy90f33fnlunaatxamjpepz0zk99qqttj97526g"

agent = Agent(
    name="alice",
    port=8000,
    seed="agent1 secret phrasexx",
    endpoint="http://127.0.0.1:8000/submit",
    resolve=AlmanacResolver(),
)

ledger = get_ledger("fetchai-testnet")
faucet_api = FaucetApi(NetworkConfig.latest_stable_testnet())

agent_balance = ledger.query_bank_balance(agent.wallet.address())

if agent_balance < 500000000000000000:
    # Add tokens to agent's wallet
    faucet_api.get_wealth(agent.wallet.address())


agent.register()


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(RECIPIENT_ADDRESS, Message(message="hello there bob"))


@agent.on_message(model=Message)
async def on_message(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")


if __name__ == "__main__":
    agent.run()
