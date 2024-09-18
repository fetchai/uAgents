from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from uagents import Model
import speech_recognition as sr


class Message(Model):
    message: str


Gemini_Address = "agent1qwg20ukwk97t989h6kc8a3sev0lvaltxakmvvn3sqz9jdjw4wsuxqa45e8l"  # replace your Gemini API key here

user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint=["http://localhost:5000/submit"],
)

fund_agent_if_low(user.wallet.address())

question_count = 0


@user.on_event("startup")
async def agent_address(ctx: Context):
    global question_count
    ctx.logger.info(user.address)
    message = str(
        "Pretend to be an interviewer, begin by asking me a question about databases Don't answer that questions yourself. Consider that each of my following prompts to you are the answers to those questions. Based on my answers, I want you to ask further questions, related to databases. Do not list out all the questions at once. Wait for me to answer the first question, and only then ask the next one. I will answer each question one at a time just ask questions one at a time. Don't generate answers for me yourself. You have to stop after 3 questions and you have to judge the answers with the model answers and rate the user harshly out of 10, but don't stop the server."
    )
    await ctx.send(Gemini_Address, Message(message=message))
    question_count += 1


@user.on_message(model=Message)
async def handle_query_response(ctx: Context, sender: str, msg: Message):
    global question_count
    if question_count < 4:
        r = sr.Recognizer()
        while True:
            with sr.Microphone() as source:
                print("Talk")
                audio_text = r.listen(source)
                print("Time over, thanks")
            try:
                print("Text: " + r.recognize_google(audio_text))
                message = r.recognize_google(audio_text)
                break
            except:
                print("Sorry, I did not get that. Please try again.")
        await ctx.send(sender, Message(message=message))
        question_count += 1
    else:
        print(
            "The Gemini agent has asked 3 questions. It will not ask any more questions."
        )
