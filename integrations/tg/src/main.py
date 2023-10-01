import asyncio
from telegram.ext import Application

from uagents import Bureau

from agents.telegram_agent import process_queue, telegram_agent
from agents.telegram_user import user_agent

# Telegram bot token
TELEGRAM_BOT_TOKEN = "YOUR_TOKEN_HERE"

if __name__ == "__main__":
    bureau = Bureau(endpoint="http://127.0.0.1:8000/submit", port=8000)
    print(f"Adding agent to Bureau: {telegram_agent.address}")
    bureau.add(telegram_agent)
    print(f"Adding user agent to Bureau: {user_agent.address}")
    bureau.add(user_agent)

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    # Other handlers can be added here

    loop = asyncio.get_event_loop()
    loop.create_task(process_queue(application.bot))
    loop.run_until_complete(bureau.run())
