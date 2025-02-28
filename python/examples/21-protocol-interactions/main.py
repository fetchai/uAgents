from uagents import Agent, Context, Model, Protocol
from uagents.protocol import ProtocolSpecification


class ProposeChat(Model):
    pass


class AcceptChat(Model):
    pass


class RejectChat(Model):
    pass


class Chat(Model):
    text: str


class EndChat(Model):
    pass


spec = ProtocolSpecification(
    interactions={
        ProposeChat: {AcceptChat, RejectChat},
        AcceptChat: {Chat, EndChat},
        RejectChat: set(),
        Chat: {Chat, EndChat},
        EndChat: set(),
    },
    roles={
        "user": {ProposeChat, Chat, EndChat},
        "agent": {AcceptChat, RejectChat, Chat, EndChat},
    },
)

user_proto = Protocol(name="ChatProtocol", version="0.1", spec=spec, role="user")
agent_proto = Protocol(name="ChatProtocol", version="0.1", spec=spec, role="agent")


print("Digest (before handlers):", user_proto.digest, "\n\n")
print("Manifest:", user_proto.manifest(), "\n\n")


@user_proto.on_message(ProposeChat)
async def propose_chat(ctx: Context, sender: str, msg: ProposeChat):
    ctx.logger.info(f"ProposeChat from {sender}")


@user_proto.on_message(Chat)
async def chat(ctx: Context, sender: str, msg: Chat):
    ctx.logger.info(f"Chat from {sender}: {msg.text}")


agent = Agent()

try:
    print("Try to include incomplete protocol in agent:")
    agent.include(user_proto)
except Exception as e:
    print(e, "\n\n")


@user_proto.on_message(EndChat)
async def end_chat(ctx: Context, sender: str, msg: EndChat):
    ctx.logger.info(f"EndChat from {sender}")


try:
    print("Try to add a handler for the wrong role:")

    @user_proto.on_message(AcceptChat)
    async def accept_chat(ctx: Context, sender: str, msg: AcceptChat):
        ctx.logger.info(f"AcceptChat from {sender}")
except Exception as e:
    print(e, "\n\n")


print("Digest (after handlers):", user_proto.digest, "\n\n")


agent.include(user_proto)
print("Successfully included complete protocol in agent")
