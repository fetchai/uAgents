# Import required libraries
import requests
from ai_engine.chitchat import ChitChatDialogue
from ai_engine.messages import DialogueMessage
from uagents import Context, Model


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


async def get_players(perfType):
    url = f"https://lichess.org/api/player/top/10/{perfType}"
    response = requests.get(url)
    data = response.json()
    return data

chitchat_dialogue = ChitChatDialogue(
    version="0.11.1",  # example 0.11.1
    storage=agent.storage,
)


@chitchat_dialogue.on_initiate_session(InitiateChitChatDialogue)
async def start_chitchat(
    ctx: Context,
    sender: str,
    msg: InitiateChitChatDialogue,
):
    ctx.logger.info(f"Received init message from {
                    sender} Session: {ctx.session}")
    # do something when the dialogue is initiated
    await ctx.send(sender, AcceptChitChatDialogue())


@chitchat_dialogue.on_start_dialogue(AcceptChitChatDialogue)
async def accepted_chitchat(
    ctx: Context,
    sender: str,
    _msg: AcceptChitChatDialogue,
):
    ctx.logger.info(
        f"session with {
            sender} was accepted. This shouldn't be called as this agent is not the initiator."
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
    if msg.user_message not in ["ultraBullet", "bullet", "blitz", "rapid", "classical", "chess960", "crazyhouse", "antichess", "atomic", "horde", "kingOfTheHill", "racingKings", "threeCheck"]:
        final_string = f'Not a valid gamemode'
    else:
        top_players = await get_players(msg.user_message)
        user_ids = [user['id'] for user in top_players['users']]
        ctx.logger.info(f"Data: {top_players}")
        final_string = f'The top 10 players are {", ".join(user_ids)}'
    try:
        await ctx.send(
            sender,
            ChitChatDialogueMessage(
                type="agent_message",
                agent_message=final_string
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
    ctx.logger.info(f"Received conclude message from: {
                    sender}; accessing history:")
    ctx.logger.info(chitchat_dialogue.get_conversation(ctx.session))


agent.include(chitchat_dialogue, publish_manifest=True)
