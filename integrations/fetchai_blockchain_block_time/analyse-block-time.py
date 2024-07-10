import io

import aiohttp
import numpy as np
import pandas as pd
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
from uagents import Agent, Context, Model, Protocol

# First generate a secure seed phrase (e.g. https://pypi.org/project/mnemonic/)
# Important: CREATE NEW SEED PHRASE FOR THIS AGENT
SEED_PHRASE = "-- analyse block time agent seed phrase --"

assert SEED_PHRASE != "-- analyse block time agent seed phrase --", "Please set a new seed phrase"

# Then go to https://agentverse.ai, register your agent in the Mailroom
# and copy the agent's mailbox key
AGENT_MAILBOX_KEY = ""

# Now your agent is ready to join the AgentVerse!
agent = Agent(
    name="data",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# Copy the address shown below
print(f"Your agent's address is: {agent.address}")


class BlockTimeAnalysisRequest(Model):
    data_url: str = Field(description="The url to the blockchain data to be analysed. You MUST use subtask to find blockchain data in CSV.")


proto = Protocol("BlockTime", "0.1.0")


async def download_blockchain_data(data_url: str) -> pd.DataFrame:
    async with aiohttp.ClientSession() as session:
        async with session.get(data_url) as response:
            response.raise_for_status()
            data = await response.text()

            df = pd.read_csv(io.StringIO(data))
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            return df


@proto.on_message(model=BlockTimeAnalysisRequest, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: BlockTimeAnalysisRequest):
    ctx.logger.info(f"Received message from {sender}: {msg.data_url}")

    blockchain_data = await download_blockchain_data(msg.data_url)
    average_block_time = np.diff(np.flip(blockchain_data['timestamp'])).mean().total_seconds()

    await ctx.send(
        sender,
        UAgentResponse(
            message=f"The average block time is {average_block_time} seconds",
            type=UAgentResponseType.FINAL,
        )
    )


agent.include(proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
