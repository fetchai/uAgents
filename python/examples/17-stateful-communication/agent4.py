"""Chit chat dialogue example"""

from asyncio import sleep

from dialogues.hardcoded_chitchat import (
    ChitChatDialogue,
    ChitChatDialogueMessage,
    InitiateChitChatDialogue,
)
from uagents import Agent, Context

CHIT_AGENT_ADDRESS = "agent1qfjvt60h0kh573fzy9mvmlsr50vff8xmdfeclfgy3g9g6qq6jxkuxh4cu3w"

agent = Agent(
    name="chat_agent",
    seed="9876543210000000004",
    port=8002,
    endpoint="http://127.0.0.1:8002/submit",
    log_level="DEBUG",
)


# instantiate the dialogues
chitchat_dialogue = ChitChatDialogue(
    version="0.1",
    agent_address=agent.address,
)


@chitchat_dialogue.on_continue_dialogue()
async def continue_chitchat(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    ctx.logger.info(f"Returning: {msg.text}")
    await ctx.send(sender, ChitChatDialogueMessage(text=msg.text))


# initiate dialogue after 5 seconds
@agent.on_event("startup")
async def start_cycle(ctx: Context):
    await sleep(5)
    await ctx.send(CHIT_AGENT_ADDRESS, InitiateChitChatDialogue())


agent.include(chitchat_dialogue)

if __name__ == "__main__":
    print(f"Agent address: {agent.address}")
    agent.run()
