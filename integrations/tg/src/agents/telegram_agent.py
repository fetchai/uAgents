import asyncio
from asyncio import Queue
from uagents import Agent, Context, Protocol
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

# Declaration of a message event handler for handling TelegramRequests and send respective response.


@telegram_agent_protocol.on_message(model=TelegramRequest, replies={TelegramResponse, Error})
async def handle_request(ctx: Context, sender: str, request: TelegramRequest):
    ctx.logger.info(f"Got request from {sender}: {request.text}")
    await message_queue.put((request.chat_id, request.text))

# Include protocol to the agent
telegram_agent.include(telegram_agent_protocol)
