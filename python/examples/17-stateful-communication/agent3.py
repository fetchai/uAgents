"""Chit chat dialogue example"""

import json

from dialogues.hardcoded_chitchat import (
    ChitChatDialogue,
    ChitChatDialogueMessage,
    ConcludeChitChatDialogue,
)
from uagents import Agent, Context

CHAT_AGENT_ADDRESS = "agent1qwvecfwc255pfqqwtjznh9qqk6skl77xc6fzw8mr3ppfex32sr0kcad62n4"

agent = Agent(
    name="chit_agent",
    seed="9876543210000000003",
    port=8001,
    endpoint="http://127.0.0.1:8001/submit",
)


# instantiate the dialogues
chitchat_dialogue = ChitChatDialogue(
    version="0.1",
    storage=agent.storage,
)

# get an overview of the dialogue structure
print("Dialogue overview:")
print(json.dumps(chitchat_dialogue.get_overview(), indent=4))
print("---")


# This is the only decorator that is needed to add to your agent with the
# hardcoded dialogue example. If you omit this decorator, the dialogue will
# emit a warning.
@chitchat_dialogue.on_continue_dialogue()
async def continue_chitchat(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    # do something when the dialogue continues
    ctx.logger.info(f"Received message: {msg.text}")
    try:
        my_msg = input("Please enter your message:\n> ")
        await ctx.send(sender, ChitChatDialogueMessage(text=my_msg))
    except EOFError:
        await ctx.send(sender, ConcludeChitChatDialogue())


agent.include(chitchat_dialogue)


if __name__ == "__main__":
    print(f"Agent address: {agent.address}")
    agent.run()
