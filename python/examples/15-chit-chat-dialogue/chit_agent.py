"""Chit chat dialogue example"""
from asyncio import sleep
import json

from dialogues.chitchat import ChitChatDialogue
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

CHAT_AGENT_ADDRESS = "agent1qgp7urkvx24a2gs8e7496fajzy78h4887vz7va4h7klzf7azzhthsz7zymu"

API_KEY = "paste your api key"

agent1 = Agent(
    name="agent1",
    seed="9876543210000000000",
    port=8001,
    agentverse=f"{API_KEY}@https://agentverse.ai",
)
agent1._logger.setLevel("DEBUG")  # pylint: disable=protected-access
fund_agent_if_low(agent1.wallet.address())


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
chitchat_dialogue1 = ChitChatDialogue(
    version="0.1",
    agent_address=agent1.address,
)

# get an overview of the dialogue structure
print("Dialogue overview:")
print(json.dumps(chitchat_dialogue1.get_overview(), indent=4))
print("---")


@chitchat_dialogue1.on_initiate_session(InitiateChitChatDialogue)
async def start_chitchat(
    ctx: Context,
    sender: str,
    _msg: InitiateChitChatDialogue,
):
    ctx.logger.info(f"Received init message from {sender}")
    # do something when the dialogue is initiated
    await ctx.send(sender, AcceptChitChatDialogue())


@chitchat_dialogue1.on_start_dialogue(AcceptChitChatDialogue)
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


@chitchat_dialogue1.on_reject_session(RejectChitChatDialogue)
async def reject_chitchat(
    ctx: Context,
    sender: str,
    _msg: RejectChitChatDialogue,
):
    # do something when the dialogue is rejected and nothing has been sent yet
    ctx.logger.info(f"Received conclude message from: {sender}")


@chitchat_dialogue1.on_continue_dialogue(ChitChatDialogueMessage)
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


@chitchat_dialogue1.on_end_session(ConcludeChitChatDialogue)
async def conclude_chitchat(
    ctx: Context,
    sender: str,
    _msg: ConcludeChitChatDialogue,
):
    # do something when the dialogue is concluded after messages have been exchanged
    ctx.logger.info(f"Received conclude message from: {sender}; accessing history:")
    ctx.logger.info(ctx.dialogue)


agent1.include(chitchat_dialogue1)


# initiate dialogue
@agent1.on_event("startup")
async def start_cycle(ctx: Context):
    await sleep(5)
    await ctx.send(CHAT_AGENT_ADDRESS, InitiateChitChatDialogue())


if __name__ == "__main__":
    print("Agent 1:", agent1.address)
    agent1.run()
