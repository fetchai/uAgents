"""Chit chat dialogue example"""
import json

from dialogues.chitchat import ChitChatDialogue
from uagents import Agent, Bureau, Context, Model
from uagents.setup import fund_agent_if_low

agent1 = Agent(name="agent1", seed="9876543210000000000")
agent1._logger.setLevel("DEBUG")  # pylint: disable=protected-access
fund_agent_if_low(agent1.wallet.address())

agent2 = Agent(name="agent2", seed="9876543210000000001")
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
chitchat_dialogue1 = ChitChatDialogue(
    version="0.1",
    agent_address=agent1.address,
)
chitchat_dialogue2 = ChitChatDialogue(
    version="0.1",
    agent_address=agent2.address,
)

# get an overview of the dialogue structure
print("Dialogue overview:")
print(json.dumps(chitchat_dialogue1.get_overview(), indent=4))
print("---")


# agent1
agent1.storage.set("message_counter", 0)
agent2.storage.set("message_counter", 0)


@chitchat_dialogue1.on_state_transition("Initiate Session", InitiateChitChatDialogue)
async def start_chitchat(
    ctx: Context,
    sender: str,
    _msg: InitiateChitChatDialogue,
):
    # do something when the dialogue is initiated
    await ctx.send(sender, AcceptChitChatDialogue())


@chitchat_dialogue1.on_state_transition("Dialogue Started", AcceptChitChatDialogue)
async def accept_chitchat(
    ctx: Context,
    sender: str,
    _msg: AcceptChitChatDialogue,
):
    # do something after the dialogue is started; e.g. send a message
    await ctx.send(sender, ChitChatDialogueMessage(text="Hello!"))


@chitchat_dialogue1.on_state_transition(
    "Session Rejected / Not Needed", RejectChitChatDialogue
)
async def reject_chitchat(
    ctx: Context,
    sender: str,
    _msg: RejectChitChatDialogue,
):
    # do something when the dialogue is rejected and nothing has been sent yet
    ctx.logger.info(f"Received conclude message from: {sender}")


@chitchat_dialogue1.on_state_transition("Dialogue Continues", ChitChatDialogueMessage)
async def continue_chitchat(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    # do something when the dialogue continues
    ctx.logger.info(f"Received message: {msg}")
    counter = agent1.storage.get("message_counter")
    if counter < 3:
        await ctx.send(
            sender,
            ChitChatDialogueMessage(text=f"Hello again #{counter}!"),
        )
        counter += 1
        agent1.storage.set("message_counter", counter)
    else:
        await ctx.send(sender, ConcludeChitChatDialogue())


@chitchat_dialogue1.on_state_transition(
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


# agent2


@chitchat_dialogue2.on_state_transition("Initiate Session", InitiateChitChatDialogue)
async def start_chitchat2(
    ctx: Context,
    sender: str,
    _msg: InitiateChitChatDialogue,
):
    # do something when the dialogue is initiated
    await ctx.send(sender, AcceptChitChatDialogue())


@chitchat_dialogue2.on_state_transition("Dialogue Started", AcceptChitChatDialogue)
async def accept_chitchat2(
    ctx: Context,
    sender: str,
    _msg: AcceptChitChatDialogue,
):
    # do something after the dialogue is started; e.g. send a message
    await ctx.send(sender, ChitChatDialogueMessage(text="Hello!"))


@chitchat_dialogue2.on_state_transition(
    "Session Rejected / Not Needed", RejectChitChatDialogue
)
async def reject_chitchat2(
    ctx: Context,
    sender: str,
    _msg: RejectChitChatDialogue,
):
    # do something when the dialogue is rejected and nothing has been sent yet
    ctx.logger.info(f"Received conclude message from: {sender}")


@chitchat_dialogue2.on_state_transition("Dialogue Continues", ChitChatDialogueMessage)
async def continue_chitchat2(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    # do something when the dialogue continues
    ctx.logger.info(f"Received message: {msg}")
    counter = agent2.storage.get("message_counter")
    if counter < 3:
        await ctx.send(
            sender,
            ChitChatDialogueMessage(text=f"Hello again #{counter}!"),
        )
        counter += 1
        agent2.storage.set("message_counter", counter)
    else:
        await ctx.send(sender, ConcludeChitChatDialogue())


@chitchat_dialogue2.on_state_transition(
    "Hang Up / End Session", ConcludeChitChatDialogue
)
async def conclude_chitchat2(
    ctx: Context,
    sender: str,
    _msg: ConcludeChitChatDialogue,
):
    # do something when the dialogue is concluded after messages have been exchanged
    ctx.logger.info(f"Received conclude message from: {sender}")


agent1.include(chitchat_dialogue1)
agent2.include(chitchat_dialogue2)


# initiate dialogue
@agent1.on_event("startup")
async def start_cycle(ctx: Context):
    await ctx.send(agent2.address, InitiateChitChatDialogue())


if __name__ == "__main__":
    bureau = Bureau(port=8080, endpoint="http://localhost:8080/submit")
    bureau.add(agent1)
    print("Agent 1:", agent1.address)
    bureau.add(agent2)
    print("Agent 2:", agent2.address)
    bureau.run()
