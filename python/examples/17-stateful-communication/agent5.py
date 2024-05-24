"""
Specific agent example for the Agentverse chit-chat dialogue.

See python/examples/17-stateful-communication/dialogues/agentverse_chitchat.py
for the dialogue implementation.
"""

from dialogues.agentverse_chitchat import (
    AgentverseChitChat,
    ChitChatDialogueMessage,
    ConcludeChitChatDialogue,
    InitiateChitChatDialogue,
)
from uagents import Agent, Context

HOSTED_AGENT_ADDRESS = "<your hosted agent address here>"

agent = Agent(
    name="Agentverse ChitChat Agent",
    seed="<your seed here>",
    port=8080,
    endpoint="http://127.0.0.1:8080/submit",
)


chitchat = AgentverseChitChat(
    storage=agent.storage,
)


@chitchat.on_start_dialogue(InitiateChitChatDialogue)
async def start_dialogue(
    ctx: Context,
    sender: str,
    msg: InitiateChitChatDialogue,
):
    """
    Start the dialogue with a message

    This function is called when the dialogue is initiated by another agent.
    """
    ctx.logger.info(f"Received init message from {sender}")
    await ctx.send(sender, ChitChatDialogueMessage(text="Hello!"))


@chitchat.on_continue_dialogue(ChitChatDialogueMessage)
async def continue_dialogue(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    """
    Continue the dialogue with a message

    Do something with the received message and send a response.
    """
    ctx.logger.info(f"Received message: {msg.text}")
    my_msg = input("Please enter your message:\n> ")

    if my_msg == "exit":
        await ctx.send(sender, ConcludeChitChatDialogue())
        return

    await ctx.send(sender, ChitChatDialogueMessage(text=my_msg))


@chitchat.on_end_session(ConcludeChitChatDialogue)
async def conclude_dialogue(
    ctx: Context,
    sender: str,
    msg: ConcludeChitChatDialogue,
):
    """
    Conclude the dialogue

    Do something when the dialogue is concluded.
    """
    ctx.logger.info(f"Received conclude message from {sender} ({msg})")


agent.include(chitchat)


@agent.on_event("startup")
async def handle_startup(ctx: Context):
    ctx.logger.info("Agent started with address: " + agent.address)
    await chitchat.start_dialogue(ctx, HOSTED_AGENT_ADDRESS, InitiateChitChatDialogue())


if __name__ == "__main__":
    agent.run()
