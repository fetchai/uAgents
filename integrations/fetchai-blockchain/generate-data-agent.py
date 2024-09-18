import aiohttp
from uuid import uuid4
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
from uagents import Agent, Context, Model, Protocol
from google.cloud import storage


# Set the bucket name and project id
# This example we will use Google Cloud Storage to store the data
BUCKET_NAME = ""
GCP_PROJECT_ID = ""


# First generate a secure seed phrase (e.g. https://pypi.org/project/mnemonic/)
# Important: CREATE NEW SEED PHRASE FOR THIS AGENT
SEED_PHRASE = "-- generate data agent seed phrase--"

assert (
    SEED_PHRASE != "-- generate data agent seed phrase--"
), "Please set a new seed phrase"

# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

# Then go to https://agentverse.ai, register your agent in the Mailroom
# and copy the agent's mailbox key
AGENT_MAILBOX_KEY = ""

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="data",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)


async def collect_blockchain_data() -> str:
    csv_data = "timestamp,height,hash,block_size,num_tx,chain_id,proposer_address\n"

    async with aiohttp.ClientSession() as session:
        async with session.get("https://rpc-fetchhub.fetch.ai/blockchain") as response:
            response.raise_for_status()
            resp = await response.json()

            for block in resp["result"]["block_metas"]:
                timestamp = block["header"]["time"]
                height = int(block["header"]["height"])
                block_hash = block["block_id"]["hash"]
                block_size = int(block["block_size"])
                num_tx = int(block["num_txs"])
                chain_id = block["header"]["chain_id"]
                proposer_address = block["header"]["proposer_address"]

                csv_data += (
                    ",".join(
                        [
                            str(timestamp),
                            str(height),
                            block_hash,
                            str(block_size),
                            str(num_tx),
                            chain_id,
                            proposer_address,
                        ]
                    )
                    + "\n"
                )

    return csv_data


class DataSetRequest(Model):
    timeframe: str = Field(
        description="The timeframe for the data. Must start with a number and be followed by either 'm' for minutes or 'h' for hours or 'd' for days or 'w' for weeks."
    )


proto = Protocol("blockchain-data", "0.1.0")


@proto.on_message(model=DataSetRequest, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: DataSetRequest):
    ctx.logger.info(f"Received message from {sender}: {msg.timeframe}")

    # let's just ignore the time frame for now, but here we can just simply parse 10d, 1w, 2h, 30m etc
    # and use that with the API to fetch the data
    blockchain_data = await collect_blockchain_data()

    destination_blob_name = f"blockchain-data-{uuid4()}.csv"

    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)  # type: storage.Blob

    blob.upload_from_string(blockchain_data, content_type="text/csv")

    await ctx.send(
        sender,
        UAgentResponse(
            message=f"The blockchain data has been generated and is available at {blob.public_url}",
            type=UAgentResponseType.FINAL,
        ),
    )


agent.include(proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
