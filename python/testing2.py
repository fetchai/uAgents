"""Testing platform"""
from src.uagents import Agent, Bureau, Context, Model
from src.uagents.experimental.dialogues.dialogue import Dialogue
from src.uagents.setup import fund_agent_if_low

agent1 = Agent(name="agent1", seed="9876543210000000000")
agent1._logger.setLevel("DEBUG")
fund_agent_if_low(agent1.wallet.address())

agent2 = Agent(name="agent2", seed="9876543210000000001")
agent2._logger.setLevel("DEBUG")
fund_agent_if_low(agent2.wallet.address())


class InitiateChitChatDialogue(Model):
    pass


class ChitChatDialogueMessage(Model):
    text: str


class ConcludeChitChatDialogue(Model):
    pass


RULESET = {
    InitiateChitChatDialogue: {ChitChatDialogueMessage, ConcludeChitChatDialogue},
    ChitChatDialogueMessage: {ChitChatDialogueMessage, ConcludeChitChatDialogue},
    ConcludeChitChatDialogue: {},
}

handled_models = set()
for model, replies in RULESET.items():
    for reply in RULESET[model]:
        handled_models.add(reply)
        assert reply in RULESET, f"Reply {reply} not in ruleset!"
# assert len(handled_models) == len(RULESET), "Not all models are handled!"
nodes_without_entry = set(RULESET.keys()).difference(handled_models)

print(nodes_without_entry)  # must be entry node, may be multiple (?)

chitchat_dialogue1 = Dialogue(
    name="chitchat",
    version="0.1",
    rules=RULESET,
    agent_address=agent1.address,
    timeout=0,
    max_nr_of_messages=10,
)
chitchat_dialogue2 = Dialogue(
    name="chitchat",
    version="0.1",
    rules=RULESET,
    agent_address=agent2.address,
    timeout=0,
    max_nr_of_messages=10,
)

# agent1

counter = 0


@chitchat_dialogue1.on_message(
    InitiateChitChatDialogue, {ChitChatDialogueMessage, ConcludeChitChatDialogue}
)
async def start_chitchat(ctx: Context, sender: str, msg: InitiateChitChatDialogue):
    await ctx.send(sender, ChitChatDialogueMessage(text="Hello!"))


@chitchat_dialogue1.on_message(
    ChitChatDialogueMessage, {ChitChatDialogueMessage, ConcludeChitChatDialogue}
)
async def bla(ctx: Context, sender: str, msg: ChitChatDialogueMessage):
    ctx.logger.info(f"Received message: {msg}")
    global counter
    if counter < 10:
        await ctx.send(sender, ChitChatDialogueMessage(text=f"Hello again #{counter}!"))
        counter += 1
    else:
        await ctx.send(sender, ConcludeChitChatDialogue())


@chitchat_dialogue1.on_message(ConcludeChitChatDialogue)
async def stop_chitchat(ctx: Context, sender: str, msg: ConcludeChitChatDialogue):
    pass


# agent2


@chitchat_dialogue2.on_message(
    InitiateChitChatDialogue, {ChitChatDialogueMessage, ConcludeChitChatDialogue}
)
async def start_chitchat2(ctx: Context, sender: str, msg: InitiateChitChatDialogue):
    await ctx.send(sender, ChitChatDialogueMessage(text="Hello!"))


@chitchat_dialogue2.on_message(
    ChitChatDialogueMessage, {ChitChatDialogueMessage, ConcludeChitChatDialogue}
)
async def bla2(ctx: Context, sender: str, msg: ChitChatDialogueMessage):
    ctx.logger.info(f"Received message: {msg}")
    global counter
    if counter < 10:
        await ctx.send(sender, ChitChatDialogueMessage(text=f"Hello again #{counter}!"))
        counter += 1
    else:
        await ctx.send(sender, ConcludeChitChatDialogue())


@chitchat_dialogue2.on_message(ConcludeChitChatDialogue)
async def stop_chitchat2(ctx: Context, sender: str, msg: ConcludeChitChatDialogue):
    pass


agent1.include(chitchat_dialogue1)
agent2.include(chitchat_dialogue2)


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
