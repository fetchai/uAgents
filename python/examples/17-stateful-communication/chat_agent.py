"""Chit chat dialogue example"""
from uagents import Agent, Context, Model

from dialogues.chitchat import ChitChatDialogue

API_KEY = "paste your api key"

agent2 = Agent(
    name="agent2",
    seed="9876543210000000001",
    port=8002,
    # agentverse=f"{API_KEY}@https://agentverse.ai",
    endpoint="http://127.0.0.1:8002/submit",
)
agent2._logger.setLevel("DEBUG")  # pylint: disable=protected-access


# define dialogue messages; each transition needs a separate message
class InitiateChitChatDialogue(Model):
    pass


class AcceptChitChatDialogue(Model):
    pass


class ChitChatDialogueMessage(Model):
    text: str


class ConcludeChitChatDialogue(Model):
    pass


class RejectChitChatDialogue(Model):
    pass


# instantiate the dialogues
chitchat_dialogue2 = ChitChatDialogue(
    version="0.1",
    agent_address=agent2.address,
)


@chitchat_dialogue2.on_initiate_session(InitiateChitChatDialogue)
async def start_chitchat(
    ctx: Context,
    sender: str,
    _msg: InitiateChitChatDialogue,
):
    ctx.logger.info(f"Received init message from {sender}")
    # do something when the dialogue is initiated
    await ctx.send(sender, AcceptChitChatDialogue())


@chitchat_dialogue2.on_start_dialogue(AcceptChitChatDialogue)
async def accept_chitchat(
    ctx: Context,
    sender: str,
    _msg: AcceptChitChatDialogue,
):
    ctx.logger.info(
        f"session with {sender} was accepted. I'll say 'Hello!' to start the ChitChat"
    )
    # do something after the dialogue is started; e.g. send a message
    await ctx.send(sender, ChitChatDialogueMessage(text="Hello!"))


@chitchat_dialogue2.on_reject_session(RejectChitChatDialogue)
async def reject_chitchat(
    ctx: Context,
    sender: str,
    _msg: RejectChitChatDialogue,
):
    # do something when the dialogue is rejected and nothing has been sent yet
    ctx.logger.info(f"Received conclude message from: {sender}")


@chitchat_dialogue2.on_continue_dialogue(ChitChatDialogueMessage)
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


@chitchat_dialogue2.on_end_session(ConcludeChitChatDialogue)
async def conclude_chitchat(
    ctx: Context,
    sender: str,
    _msg: ConcludeChitChatDialogue,
):
    # do something when the dialogue is concluded after messages have been exchanged
    ctx.logger.info(f"Received conclude message from: {sender}; accessing history:")
    ctx.logger.info(ctx.dialogue)


agent2.include(chitchat_dialogue2)


if __name__ == "__main__":
    print("Agent 2:", agent2.address)
    agent2.run()
