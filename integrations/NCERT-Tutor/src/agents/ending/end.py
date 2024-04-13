 
# Here we demonstrate how we can create a question reading system agent that is compatible with DeltaV
    
# After running this agent, it can be registered to DeltaV on Agentverse Services tab. For registration you will have to use the agent's address
 
# Import required libraries
import requests
from uagents import Model, Protocol, Agent, Context
from ai_engine import UAgentResponse, UAgentResponseType
from uagents.setup import fund_agent_if_low
from pydantic import BaseModel
agent = Agent(
    name="Question System", 
    seed="your_agent_seed_hereasdasdasdas", 
    port=8003, 
    endpoint="http://localhost:8003/submit"
    )
class SharedLinkResponse(BaseModel):
    secure_url: str

class Response(Model):
    summary: str
    question_bank: str
    answer_key: str
    sender : str

# Define Protocol for question reading system
end_protocol = Protocol("End System")
 
fund_agent_if_low(agent.wallet.address())

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("End System Agent Started")
    ctx.logger.info(f"{agent.address}")



def send_shared_link_data(data: Response) -> str:
    url = 'https://ncert-tutor-dev-dbkt.3.us-1.fl0.io/sharedlink'
    response = requests.post(url, json=data.dict())

    if response.status_code == 200:
        return response.json()
    else:
        return None

   
# Define a handler for the Question system protocol
@end_protocol.on_message(model=Response, replies = UAgentResponse)
async def on_question_request(ctx: Context,sender: str, msg: Response):
    url = send_shared_link_data(msg)
    if url is not None:
        message = f'{msg.summary}\n{msg.question_bank}\n<a href={url}>'
    else:
        message = f'{msg.summary}\n{msg.question_bank}\n{msg.answer_key}'
    

    #Printing the question response on logger
    ctx.logger.info(f"Received question request from {sender}")
    ctx.logger.info(f"End Message: {message}")
    #Creating hyperlink and sending final response to the DeltaV GUI
    await ctx.send(msg.sender, UAgentResponse(message = message, type = UAgentResponseType.FINAL))
    return
 
# Include the End Question protocol in your agent
agent.include(end_protocol)


if __name__ == "__main__":
   agent.run()