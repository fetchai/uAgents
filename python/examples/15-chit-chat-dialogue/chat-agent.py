"""Chit chat dialogue example"""
import json

from dialogues.chitchat import ChitChatDialogue
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

API_KEY = "paste your api key"

agent2 = Agent(
    name="agent2", 
    seed="9876543210000000001", 
    port=8002,
    agentverse=f"{API_KEY}@https://agentverse.ai"
    )

agent2._logger.setLevel("DEBUG")  # pylint: disable=protected-access
fund_agent_if_low(agent2.wallet.address())


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

@chitchat_dialogue2.on_state_transition("Initiate Session", InitiateChitChatDialogue)
async def start_chitchat(
    ctx: Context,
    sender: str,
    _msg: InitiateChitChatDialogue,
):
    ctx.logger.info(f"Received init message from {sender}")
    # do something when the dialogue is initiated
    await ctx.send(sender, AcceptChitChatDialogue())


@chitchat_dialogue2.on_state_transition("Dialogue Started", AcceptChitChatDialogue)
async def accept_chitchat(
    ctx: Context,
    sender: str,
    _msg: AcceptChitChatDialogue,
):
    ctx.logger.info(f"session with {sender} was accepted. I'll say 'Hello!' to start the ChitChat")
    # do something after the dialogue is started; e.g. send a message
    await ctx.send(sender, ChitChatDialogueMessage(text="Hello!"))


@chitchat_dialogue2.on_state_transition(
    "Session Rejected / Not Needed", RejectChitChatDialogue
)
async def reject_chitchat(
    ctx: Context,
    sender: str,
    _msg: RejectChitChatDialogue,
):
    # do something when the dialogue is rejected and nothing has been sent yet
    ctx.logger.info(f"Received conclude message from: {sender}")


@chitchat_dialogue2.on_state_transition("Dialogue Continues", ChitChatDialogueMessage)
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
        


@chitchat_dialogue2.on_state_transition(
    "Hang Up / End Session", ConcludeChitChatDialogue
)
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
