"""AI Engine Chit chat dialogue example"""

import json

from ai_engine.chitchat import ChitChatDialogue
from ai_engine.messages import DialogueMessage
from uagents import Agent, Context, Model


agent = Agent(
    name="chat_agent",
    seed="ai-engine-example-seed-1234567893-",
    port=8111,
    endpoint="http://127.0.0.1:8111/submit",
    agentverse="https://staging.agentverse.ai",
)


# define dialogue messages; each transition needs a separate message
class InitiateChitChatDialogue(Model):
    """I initiate ChitChat dialogue request"""

    pass


class AcceptChitChatDialogue(Model):
    """I accept ChitChat dialogue request"""

    pass


class ChitChatDialogueMessage(DialogueMessage):
    """ChitChat dialogue message"""

    pass


class ConcludeChitChatDialogue(Model):
    """I conclude ChitChat dialogue request"""

    pass


class RejectChitChatDialogue(Model):
    """I reject ChitChat dialogue request"""

    pass


# instantiate the dialogues
chitchat_dialogue = ChitChatDialogue(
    version="0.1",
    storage=agent.storage,
)

# get an overview of the dialogue structure
print("Dialogue overview:")
print(json.dumps(chitchat_dialogue.get_overview(), indent=4))
print("---")


@chitchat_dialogue.on_initiate_session(InitiateChitChatDialogue)
async def start_chitchat(
    ctx: Context,
    sender: str,
    _msg: InitiateChitChatDialogue,
):
    ctx.logger.info(f"Received init message from {sender} Session: {ctx.session}")
    # do something when the dialogue is initiated
    await ctx.send(sender, AcceptChitChatDialogue())


@chitchat_dialogue.on_start_dialogue(AcceptChitChatDialogue)
async def accepted_chitchat(
    ctx: Context,
    sender: str,
    _msg: AcceptChitChatDialogue,
):
    ctx.logger.info(
        f"session with {sender} was accepted. This shouldn't be called as this agent is not the initiator."
    )


@chitchat_dialogue.on_reject_session(RejectChitChatDialogue)
async def reject_chitchat(
    ctx: Context,
    sender: str,
    _msg: RejectChitChatDialogue,
):
    # do something when the dialogue is rejected and nothing has been sent yet
    ctx.logger.info(f"Received conclude message from: {sender}")


@chitchat_dialogue.on_continue_dialogue(ChitChatDialogueMessage)
async def continue_chitchat(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    # do something when the dialogue continues
    ctx.logger.info(f"Received message: {msg.user_message} from: {sender}")
    try:
        await ctx.send(
            sender,
            ChitChatDialogueMessage(
                type="agent_message",
                agent_message=f"I've received your message: {msg.user_message}!",
            ),
        )
    except EOFError:
        await ctx.send(sender, ConcludeChitChatDialogue())


@chitchat_dialogue.on_end_session(ConcludeChitChatDialogue)
async def conclude_chitchat(
    ctx: Context,
    sender: str,
    _msg: ConcludeChitChatDialogue,
):
    # do something when the dialogue is concluded after messages have been exchanged
    ctx.logger.info(f"Received conclude message from: {sender}; accessing history:")
    ctx.logger.info(ctx.dialogue)


agent.include(chitchat_dialogue, publish_manifest=True)


if __name__ == "__main__":
    print(f"Agent address: {agent.address}")
    agent.run()
