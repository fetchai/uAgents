# Importing necessary libraries
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from uagents import Model
import google.generativeai as genai


# Defining a model for messages
class Message(Model):
    message: str

# Defining the user agent
Gemini_agent = Agent(
    name="Gemini Agent",
    port=8001,
    seed="Gemini Agent secret phrase",
    endpoint=["http://localhost:8001/submit"],
)
 
# Funding the user agent if its wallet balance is low
fund_agent_if_low(Gemini_agent.wallet.address())

# Configuring the API key for Google's generative AI service
genai.configure(api_key='') #replace your gemini API key here
    
# Initializing the generative model with a specific model name
model = genai.GenerativeModel('gemini-pro')
    
# Starting a new chat session
chat = model.start_chat(history=[])

print("Chat session has started. Type 'quit' to exit.")

# Function to handle incoming messages
async def handle_message(message):
   
    while True:
        # Get user input
        user_message = message
        
        # Check if the user wants to quit the conversation
        if user_message.lower() == 'quit':
            return "Exiting chat session."
            
        # Send the message to the chat session and receive a streamed response
        response = chat.send_message(user_message, stream=True)
        
        # Initialize an empty string to accumulate the response text
        full_response_text = ""
        
        # Accumulate the chunks of text
        for chunk in response:
            full_response_text += chunk.text
            
        # Print the accumulated response as a single paragraph
        message = "Gemini: " + full_response_text
        return message
        
# Event handler for agent startup
@Gemini_agent.on_event('startup')
async def address(ctx: Context):
    # Logging the agent's address
    ctx.logger.info(Gemini_agent.address)

# Handler for query given by user
@Gemini_agent.on_message(model=Message)
async def handle_query_response(ctx: Context, sender: str, msg: Message):
    # Handling the incoming message
    message = await handle_message(msg.message)
    
    # Logging the response
    ctx.logger.info(message)
    
    # Sending the response back to the sender
    await ctx.send(sender, Message(message=message))