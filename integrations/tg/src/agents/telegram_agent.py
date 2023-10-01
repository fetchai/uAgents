import asyncio
from asyncio import Queue
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from uagents import Agent, Context, Protocol, Model
from messages.basic import TelegramRequest, TelegramResponse, Error
from uagents.setup import fund_agent_if_low

# Asynchronous queue to store messages to be sent
message_queue = Queue()

# Creating the agent and funding it if necessary
telegram_agent = Agent(
    name="telegram_agent",
    seed="test seed for telegram agent",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)
fund_agent_if_low(telegram_agent.wallet.address())

# Protocol declaration for TelegramRequests
telegram_agent_protocol = Protocol("TelegramRequest")

# Function to process the message queue


async def process_queue(bot):
    while True:
        if not message_queue.empty():
            chat_id, text = await message_queue.get()
            await bot.send_message(chat_id=chat_id, text=text)
        await asyncio.sleep(5)


async def start_callback(update, context):
    await message_queue.put((update.effective_chat.id, "Hello from agent"))

# Declaration of a message event handler for handling TelegramRequests and send respective response.


@telegram_agent_protocol.on_message(model=TelegramRequest, replies={TelegramResponse, Error})
async def handle_request(ctx: Context, sender: str, request: TelegramRequest):
    ctx.logger.info(f"Got request from {sender}: {request.text}")
    print("trying to send")
    await message_queue.put((request.chat_id, "Your message here"))
    print("sent")

# Include protocol to the agent
telegram_agent.include(telegram_agent_protocol)
