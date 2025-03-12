import unittest

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

user_proto_from_handlers = Protocol(name="ChatProtocol", version="0.1")


@user_proto_from_handlers.on_message(ProposeChat, replies={AcceptChat, RejectChat})
async def propose_chat(ctx: Context, sender: str, msg: ProposeChat):
    ctx.logger.info(f"ProposeChat from {sender}")


@user_proto_from_handlers.on_message(Chat, replies={Chat, EndChat})
async def chat(ctx: Context, sender: str, msg: Chat):
    ctx.logger.info(f"Chat from {sender}: {msg.text}")


@user_proto_from_handlers.on_message(EndChat, replies=set())
async def end_chat(ctx: Context, sender: str, msg: EndChat):
    ctx.logger.info(f"EndChat from {sender}")


user = Agent()
agent = Agent()


class TestProtocolSpec(unittest.TestCase):
    def test_add_incomplete_protocol(self):
        with self.assertRaises(RuntimeError):
            user.include(user_proto)

    def test_add_handler_for_wrong_role(self):
        with self.assertRaises(ValueError):

            @user_proto.on_message(AcceptChat)
            async def accept_chat(ctx: Context, sender: str, msg: AcceptChat):
                ctx.logger.info(f"AcceptChat from {sender}")

    def test_digest_from_spec_same_as_from_handlers(self):
        self.assertEqual(user_proto.digest, user_proto_from_handlers.digest)

    def test_include_complete_protocol(self):
        @agent_proto.on_message(AcceptChat)
        async def accept_chat(ctx: Context, sender: str, msg: AcceptChat):
            ctx.logger.info(f"AcceptChat from {sender}")

        @agent_proto.on_message(RejectChat)
        async def reject_chat(ctx: Context, sender: str, msg: RejectChat):
            ctx.logger.info(f"RejectChat from {sender}")

        @agent_proto.on_message(Chat)
        async def chat(ctx: Context, sender: str, msg: Chat):
            ctx.logger.info(f"Chat from {sender}: {msg.text}")

        @agent_proto.on_message(EndChat)
        async def end_chat(ctx: Context, sender: str, msg: EndChat):
            ctx.logger.info(f"EndChat from {sender}")

        agent.include(agent_proto)
        self.assertIn(agent_proto.digest, agent.protocols)

    def test_protocol_roles(self):
        self.assertEqual(len(user_proto._models), 3)
        self.assertEqual(len(agent_proto._models), 4)

    def test_protocol_wrong_role_messages(self):
        class NotInProtocol(Model):
            pass

        with self.assertRaises(ValueError):
            ProtocolSpecification(
                interactions={Chat: set()},
                roles={"user": {NotInProtocol}},
            )
