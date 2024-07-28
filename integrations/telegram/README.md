# Telegram Agent

The Telegram Agent is a Python agent that serves as an intermediary between other agents in your system and a Telegram bot for sending messages.

## Prerequisites

- Python (v3.9+ recommended)
- Poetry (A Python packaging and dependency management tool)

## Setup
- pip install uAgents
- pip install telegram
- pip install python-telegram-bot

### Obtain Telegram Bot Token

1. Go to `@BotFather` on Telegram.
2. Create a new bot or use an existing one to get the token.
3. Remember your bot token and put it later in TELEGRAM_BOT_TOKEN var.
### Variables Setup

\`\`\`
TELEGRAM_BOT_TOKEN="Your_Telegram_Bot_Token_Here"
\`\`\`

## Running The Script

To run the agent, use the following command:

\`\`\`bash
poetry run python main.py
\`\`\`

or

\`\`\`bash
python3 main.py
\`\`\`
### Expected Output

Look for the following output in the console:

\`\`\`
Agent initialized: {agent_address}
\`\`\`

Copy the `{agent_address}` and use it wherever needed in your system to interact with this Telegram agent.

## Inter-agent Communication

To send messages from another agent, you need to provide:

1. **Chat ID**: The unique identifier for the chat.
2. **Message**: The actual text to be sent.

Optionally:

3. **Bot Token**: If working with multiple bots.

This will allow any agent in your system to communicate via Telegram by interacting with this Telegram agent.