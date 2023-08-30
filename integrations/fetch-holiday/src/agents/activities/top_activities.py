from langchain.chat_models import ChatOpenAI
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate
from messages import UAgentResponse, UAgentResponseType, TopActivities, KeyValue
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
import os


TOP_ACTIVITIES_SEED = os.getenv("TOP_ACTIVITIES_SEED", "top_activities really secret phrase :)")

agent = Agent(
    name="top_activities",
    seed=TOP_ACTIVITIES_SEED
)

fund_agent_if_low(agent.wallet.address())

output_parser = CommaSeparatedListOutputParser()
format_instructions = output_parser.get_format_instructions()
prompt = PromptTemplate(
    template="""
        You are an expert AI in suggesting travel, holiday activities based on the date and city specified in user input.\n
        The question that SerpAPI has to answer: What are the top 5 tourist activities in {city} on {date}?\n
        {preferred_activities_str}\n
        You should find tourist attractions and programs which are available exactly on the specified date.\n
        {format_instructions}""",
    input_variables=["city", "date", "preferred_activities_str"],
    partial_variables={"format_instructions": format_instructions}
)

llm = ChatOpenAI(temperature=0.1)
tools = load_tools(["serpapi"], llm=llm)
langchain_agent = initialize_agent(tools, llm, agent="chat-zero-shot-react-description", verbose=True)

top_activities_protocol = Protocol("TopActivities")

@top_activities_protocol.on_message(model=TopActivities, replies=UAgentResponse)
async def get_top_activity(ctx: Context, sender: str, msg: TopActivities):
    ctx.logger.info(f"Received message from {sender}, session: {ctx.session}")

    preferred_activities_str = f"You should only offer programs and activities related to {msg.preferred_activities}" if msg.preferred_activities else ""
    _input = prompt.format(city=msg.city, date=msg.date, preferred_activities_str = preferred_activities_str)
    try:
        output = await langchain_agent.arun(_input)
        result = output_parser.parse(output)
        options = list(map(lambda x: KeyValue(key=x, value=x), result))
        ctx.logger.info(f"Agent executed and got following result: {result}. Mapped to options: {options}")
        await ctx.send(
            sender,
            UAgentResponse(
                options=options,
                type=UAgentResponseType.FINAL_OPTIONS,
            )
        )
    except Exception as exc:
      ctx.logger.warn(exc)
      await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))

agent.include(top_activities_protocol)
