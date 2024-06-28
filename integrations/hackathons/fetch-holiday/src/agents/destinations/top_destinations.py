from uagents import Agent, Context, Protocol
from messages import TopDestinations, UAgentResponse, UAgentResponseType, KeyValue
from uagents.setup import fund_agent_if_low
from utils.llm import get_llm
import os


TOP_DESTINATIONS_SEED = os.getenv("TOP_DESTINATIONS_SEED", "top_destinations really secret phrase :)")

agent = Agent(
    name="top_destinations",
    seed=TOP_DESTINATIONS_SEED
)

fund_agent_if_low(agent.wallet.address())

llm = get_llm()
top_destinations_protocol = Protocol("TopDestinations")

@top_destinations_protocol.on_message(model=TopDestinations, replies=UAgentResponse)
async def get_top_destinations(ctx: Context, sender: str, msg: TopDestinations):
    ctx.logger.info(f"Received message from {sender}, session: {ctx.session}")
    prompt = f"""You are an expert AI in suggesting travel, holiday destination based on some user input.
User input might not be provided, in which case suggest popular destinations. 
If user input is present, then suggest destinations based on user input.
The response should be a list of destinations, each destination should have information about why it is a good destination. 
After listing all the suggestions say END. Every destination should be separated by a new line.

Example:
User input: I want to go to a place with good weather and beaches.
Response:
1. Goa, India. Goa is a popular destination for tourists. It has good weather and beaches.
2. Malé, Maldives. Maldives is a popular destination for tourists. It has good weather and beaches.
END

User preferences: {msg.preferences}
"""
    try:
        response = await llm.complete("", prompt, "Response:", max_tokens=500, stop=["END"])
        result = response.strip()
        result = result.split("\n")
        await ctx.send(
            sender,
            UAgentResponse(
                options=list(map(lambda x: KeyValue(key=x, value=x), result)),
                type=UAgentResponseType.FINAL_OPTIONS
            )
        )
    except Exception as exc:
        ctx.logger.warn(exc)
        await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))

agent.include(top_destinations_protocol)
