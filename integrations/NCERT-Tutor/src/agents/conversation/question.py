 
# Here we demonstrate how we can create a question reading system agent that is compatible with DeltaV
    
# After running this agent, it can be registered to DeltaV on Agentverse Services tab. For registration you will have to use the agent's address
 
# Import required libraries
import requests
from uagents import Model, Protocol, Agent, Context
from ai_engine import UAgentResponse, UAgentResponseType
from uagents.setup import fund_agent_if_low

agent = Agent(
    name="Question System", 
    seed="your_agent_seed_here", 
    port=8000, 
    endpoint="http://localhost:8000/submit"
    )

# Define Question Reading Model
class Question(Model):
    question : str
    chapter: int
    subject: str
    standard: int
    sender : str

class Inputmod(Model):
    question : str
    chapter: int
    subject: str
    standard: int

class End(Model):
    msg: str

# Define Protocol for question reading system
question_protocol = Protocol("Question System")
 
fund_agent_if_low(agent.wallet.address())

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Question System Agent Started")
    ctx.logger.info(f"{agent.address}")
    await ctx.send("agent1qvwqu6a0km09mq4f6j6kmke9smswmgcergmml9a54av9449rqtmmxy4qwe6", Question(question = "Can you provide a summary of the chapter 'colors' from standard 3 English?", chapter = 101, subject = "english", standard = 3, sender = agent.address))
    
# Define a handler for the Question system protocol

@question_protocol.on_message(model=Inputmod, replies = UAgentResponse)
async def on_question_request(ctx: Context, sender: str, msg: Inputmod):
    #Printing the question response on logger
    ctx.logger.info(f"Received question request from {sender}")
    ctx.logger.info(f"Question: {msg.question}, Chapter: {msg.chapter}, Subject: {msg.subject}, Standard: {msg.standard}")
    await ctx.send("agent1q26wap4wv5fwteg3y6zkcnsxgg9argekfmcp2z2fdv9dek5xrkhu2e5z8zu", Question(question = msg.question, chapter = msg.chapter, subject = msg.subject, standard = msg.standard, sender = sender))
    #Creating hyperlink and sending final response to the DeltaV GUI
    message = f"you asked for help with chapter: {msg.chapter} from {msg.standard} in {msg.subject}"
    await ctx.send(sender, UAgentResponse(message = 'Hmm...', type = UAgentResponseType.FINAL))
 
 
 
# Include the Generate Question protocol in your agent
agent.include(question_protocol)


if __name__ == "__main__":
    agent.run()