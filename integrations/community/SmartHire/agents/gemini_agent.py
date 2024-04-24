from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from uagents import Model
import google.generativeai as genai


class Message(Model):
    message: str

Gemini_agent = Agent(
    name="Gemini Agent",
    port=8001,
    seed="Gemini Agent secret phrase",
    endpoint=["http://localhost:8001/submit"],
)
 
fund_agent_if_low(Gemini_agent.wallet.address())

genai.configure(api_key='') #replace your gemini API key here
    
model = genai.GenerativeModel('gemini-pro')
    
chat = model.start_chat(history=[])

print("Chat session has started. Type 'quit' to exit.")

async def handle_message(message):
   
    while True:
        user_message = message
        
        if user_message.lower() == 'quit':
            return "Exiting chat session."
            
        response = chat.send_message(user_message, stream=True)
        
        full_response_text = ""
        
        for chunk in response:
            full_response_text += chunk.text
            
        message = "Gemini: " + full_response_text
        return message
        
@Gemini_agent.on_event('startup')
async def address(ctx: Context):
    ctx.logger.info(Gemini_agent.address)

@Gemini_agent.on_message(model=Message)
async def handle_query_response(ctx: Context, sender: str, msg: Message):
    message = await handle_message(msg.message)
    
    ctx.logger.info(message)
    
    await ctx.send(sender, Message(message=message))
