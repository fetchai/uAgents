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

# Generated from the Protocol's previous manifest implementation
USER_PROTOCOL_MANIFEST = {
    "version": "1.0",
    "metadata": {
        "name": "ChatProtocol",
        "version": "0.1.0",
        "digest": "proto:4cd9a2a7be8b56192b97464c6c59bbcf483a9e97c41519d5aff229d9a6fc0972",
    },
    "models": [
        {
            "digest": "model:73e6dc00dc6d6142f6ad445f41be357c2b97c7136cece363c43496c800d8f11e",
            "schema": {"title": "ProposeChat", "type": "object", "properties": {}},
        },
        {
            "digest": "model:82ff6e4e880c1257fc35e1be1932c268ca5910e488403c8d51b4fe5ef26d9846",
            "schema": {
                "title": "Chat",
                "type": "object",
                "properties": {"text": {"title": "Text", "type": "string"}},
                "required": ["text"],
            },
        },
        {
            "digest": "model:576c72a1611982d06f4dcbd5cecf847a1109e894704482e0d1f721dd2be2df50",
            "schema": {"title": "EndChat", "type": "object", "properties": {}},
        },
        {
            "digest": "model:04c3f9c389fff2e9e58fbdd56193d958593b8b4c7bd3c700acc6ef7bb8c094c0",
            "schema": {"title": "RejectChat", "type": "object", "properties": {}},
        },
        {
            "digest": "model:0551174733a6b2271f32f9b0d1f760715590a6e88e9886fd20c9391a3b524abc",
            "schema": {"title": "AcceptChat", "type": "object", "properties": {}},
        },
    ],
    "interactions": [
        {
            "type": "normal",
            "request": "model:73e6dc00dc6d6142f6ad445f41be357c2b97c7136cece363c43496c800d8f11e",
            "responses": [
                "model:04c3f9c389fff2e9e58fbdd56193d958593b8b4c7bd3c700acc6ef7bb8c094c0",
                "model:0551174733a6b2271f32f9b0d1f760715590a6e88e9886fd20c9391a3b524abc",
            ],
        },
        {
            "type": "normal",
            "request": "model:82ff6e4e880c1257fc35e1be1932c268ca5910e488403c8d51b4fe5ef26d9846",
            "responses": [
                "model:576c72a1611982d06f4dcbd5cecf847a1109e894704482e0d1f721dd2be2df50",
                "model:82ff6e4e880c1257fc35e1be1932c268ca5910e488403c8d51b4fe5ef26d9846",
            ],
        },
        {
            "type": "normal",
            "request": "model:576c72a1611982d06f4dcbd5cecf847a1109e894704482e0d1f721dd2be2df50",
            "responses": [],
        },
    ],
}


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

    def test_proto_spec_manifest_same_as_orig_proto_manifest(self):
        spec_manifest_user = user_proto.spec.manifest(role="user")
        self.assertEqual(spec_manifest_user, USER_PROTOCOL_MANIFEST)
