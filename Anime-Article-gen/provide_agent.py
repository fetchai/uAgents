from uagents import Agent, Context, Model, Protocol  # Importing necessary classes from the uagents module
from pydantic import Field  # Importing the Field class from pydantic for model validation
from ai_engine import UAgentResponse, UAgentResponseType  # Importing classes from the ai_engine module

# Define the model for the message containing anime/manga choice and genre
class anorman(Model):
    choice: str = Field(description="The choice. Must be ANIME or MANGA.")
    genre: str = Field(description="The input must be a valid anime/manga genre")

# Define the model for the message to be sent between agents
class Message(Model):
    message: str

# Replace with the PROCESS_ADDRESS generated elsewhere
PROCESS_ADDRESS = "your_agent_address_here"

# Replace with your second seed phrase
SEED_PHRASE = "your_seed_phrase_here"

# Replace with your agent's mailbox key from https://agentverse.ai
AGENT_MAILBOX_KEY = "your_mailbox_key_here"

# Create an agent named "bob" with the specified seed phrase and mailbox
agent = Agent(
    name="bob",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# Define a protocol named "animang_protocol" for handling messages of type "anorman"
animang_protocol = Protocol("anorman")

# Define a handler for the "gentop10" event triggered by receiving a message of type "anorman"
@animang_protocol.on_message(model=anorman, replies={UAgentResponse})
async def gentop10(ctx: Context, sender: str, msg: anorman):
    # Log event information
    ctx.logger.info("providing input to process agent")
    # Send the received message to the specified address (PROCESS_ADDRESS)
    await ctx.send(PROCESS_ADDRESS, anorman(choice=msg.choice, genre=msg.genre))
    # Initialize message variable
    mg = " "
    # Define a handler for the "on_message" event triggered by receiving a message of type "Message"
    @agent.on_message(model=Message, replies={Message})
    async def on_message(cntx: Context, sendr: str, mgs: Message):
        # Set the message content received from process agent
        mg = gms.message
        # Log the received data
        cntx.logger.info(f"Received data from process_agent")

    # Send the response message containing the processed data back to the sender
    await ctx.send(sender, UAgentResponse(message=mg, type=UAgentResponseType.FINAL))

# Include the defined protocol in the agent and publish the manifest
agent.include(animang_protocol, publish_manifest=True)
