# # Importing necessary libraries from uagents package
# from uagents import Agent, Context
# from uagents.setup import fund_agent_if_low
# from uagents import Model

# # Defining a model for messages
# class Message(Model):
#     message: str

# # Specifying the address of the gemini ai agent
# Gemini_Address = "" # replace your Gemini API key here

# # Defining the user agent with specific configuration details
# user = Agent(
#     name="user",
#     port=8000,
#     seed="user secret phrase",
#     endpoint=["http://localhost:5000/submit"],
# )
 
# # Checking and funding the user agent's wallet if its balance is low
# fund_agent_if_low(user.wallet.address())
 
# # Add a counter to keep track of the number of questions asked
# question_count = 0

# # Event handler for the user agent's startup event
# @user.on_event('startup')
# async def agent_address(ctx: Context):
#     global question_count
#     # Logging the user agent's address
#     ctx.logger.info(user.address)
#     # Prompting for user input and sending it as a message to the gemini agent
#     message = str("Pretend to be an interviewer, begin by asking me a question about databases. Consider that each of my following prompts to you are the answers to those questions. Based on my answers, I want you to ask further questions, related to databases. Do not list out all the questions at once. Wait for me to answer the first question, and only then ask the next one. I will answer each question one by one just ask questions one at a time. Don't generate answers for me yourself. You have to stop after 3 questions and you have to judge the answers with the model answers and rate the user harshly, but don't stop the server.")
#     await ctx.send(Gemini_Address, Message(message=message))
#     question_count += 1

# # Handler for receiving messages from gemini agent and sending new request
# @user.on_message(model=Message)
# async def handle_query_response(ctx: Context, sender: str, msg: Message):
#     global question_count
#     # Check if the question count is less than 3 before prompting for the next user input
#     if question_count < 4:
#         # Prompting for the next user input upon receiving a message
#         message = str(input('You:'))
#         # Sending the user's message back to the sender (restaurant agent)
#         await ctx.send(sender, Message(message=message))
#         question_count += 1
#     else:
#         print("The Gemini agent has asked 3 questions. It will not ask any more questions.")



# Importing necessary libraries
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from uagents import Model
import speech_recognition as sr

# Defining a model for messages
class Message(Model):
    message: str

# Specifying the address of the gemini ai agent
Gemini_Address = "agent1qwg20ukwk97t989h6kc8a3sev0lvaltxakmvvn3sqz9jdjw4wsuxqa45e8l" # replace your Gemini API key here

# Defining the user agent with specific configuration details
user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint=["http://localhost:5000/submit"],
)

# Checking and funding the user agent's wallet if its balance is low
fund_agent_if_low(user.wallet.address())

# Add a counter to keep track of the number of questions asked
question_count = 0

# Event handler for the user agent's startup event
@user.on_event('startup')
async def agent_address(ctx: Context):
    global question_count
    # Logging the user agent's address
    ctx.logger.info(user.address)
    # Prompting for user input and sending it as a message to the gemini agent
    message = str("Pretend to be an interviewer, begin by asking me a question about databases Don't answer that questions yourself. Consider that each of my following prompts to you are the answers to those questions. Based on my answers, I want you to ask further questions, related to databases. Do not list out all the questions at once. Wait for me to answer the first question, and only then ask the next one. I will answer each question one at a time just ask questions one at a time. Don't generate answers for me yourself. You have to stop after 3 questions and you have to judge the answers with the model answers and rate the user harshly out of 10, but don't stop the server.")
    await ctx.send(Gemini_Address, Message(message=message))
    question_count += 1

# Handler for receiving messages from gemini agent and sending new request
@user.on_message(model=Message)
async def handle_query_response(ctx: Context, sender: str, msg: Message):
    global question_count
    # Check if the question count is less than 3 before prompting for the next user input
    if question_count < 4:
        # Initialize recognizer class (for recognizing the speech)
        r = sr.Recognizer()
        # Reading Microphone as source
        # listening the speech and store in audio_text variable
        while True:
            with sr.Microphone() as source:
                print("Talk")
                audio_text = r.listen(source)
                print("Time over, thanks")
            # recoginize_() method will throw a request error if the API is unreachable, hence using exception handling
            try:
                # using google speech recognition
                print("Text: "+r.recognize_google(audio_text))
                message = r.recognize_google(audio_text)
                break
            except:
                print("Sorry, I did not get that. Please try again.")
        # Sending the user's message back to the sender (restaurant agent)
        await ctx.send(sender, Message(message=message))
        question_count += 1
    else:
        print("The Gemini agent has asked 3 questions. It will not ask any more questions.")
