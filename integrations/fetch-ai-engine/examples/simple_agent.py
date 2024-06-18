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


class ChitChatDialogueMessage(DialogueMessage):
    """ChitChat dialogue message"""

    pass


class ConcludeChitChatDialogue(Model):
    """I conclude ChitChat dialogue request"""

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


@agent.on_event("startup")
async def start(ctx: Context):
    print(
        f"aiengine chitchat manifest: >>>>>>>>>>>>>>>>>>\n{chitchat_dialogue.manifest()}"
    )


@chitchat_dialogue.on_start_dialogue(InitiateChitChatDialogue)
async def accepted_chitchat(
    ctx: Context,
    sender: str,
    _msg: InitiateChitChatDialogue,
):
    ctx.logger.info(
        f"session with {sender} was accepted. This shouldn't be called as this agent is not the initiator."
    )


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
    ctx.logger.info(chitchat_dialogue.get_conversation(ctx.session))


agent.include(chitchat_dialogue, publish_manifest=True)


if __name__ == "__main__":
    print(f"Agent address: {agent.address}")
    agent.run()
