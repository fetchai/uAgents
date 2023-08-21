# pylint: disable=protected-access
import unittest
from typing import Callable


from uagents import Agent, Model, Protocol


class Message(Model):
    message: str


class Query(Model):
    query: str


MESSAGE_DIGEST = Model.build_schema_digest(Message)
QUERY_DIGEST = Model.build_schema_digest(Query)


alice = Agent(name="alice", seed="alice recovery password")
protocol = Protocol(name="test", version="1.1.1")


class TestAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = alice
        self.protocol = protocol
        return super().setUp()

    def test_protocol_init(self):
        self.assertEqual(self.protocol.name, "test")
        self.assertEqual(self.protocol.version, "1.1.1")

    def test_protocol_on_interval(self):
        @self.protocol.on_interval(period=10)
        def _(_ctx):
            pass

        interval = self.protocol._interval_handlers[0]
        self.assertTrue(isinstance(interval[0], Callable))
        self.assertEqual(interval[1], 10)

    def test_protocol_on_signed_message(self):
        @self.protocol.on_message(Message)
        def _(_ctx, _sender, _msg):
            pass

        models = self.protocol._models
        signed_msg_handlers = self.protocol._signed_message_handlers
        unsigned_msg_handlers = self.protocol._unsigned_message_handlers

        self.assertEqual(len(models), 1)
        self.assertEqual(len(unsigned_msg_handlers), 0)
        self.assertEqual(len(signed_msg_handlers), 1)
        self.assertTrue(isinstance(signed_msg_handlers[MESSAGE_DIGEST], Callable))
        self.assertTrue(MESSAGE_DIGEST in self.protocol.models)

    def test_protocol_on_unsigned_message(self):
        @self.protocol.on_message(Query, allow_unverified=True)
        def _(_ctx, _sender, _msg):
            pass

        models = self.protocol._models
        signed_msg_handlers = self.protocol._signed_message_handlers
        unsigned_msg_handlers = self.protocol._unsigned_message_handlers

        self.assertEqual(len(models), 2)
        self.assertEqual(len(unsigned_msg_handlers), 1)
        self.assertEqual(len(signed_msg_handlers), 1)
        self.assertTrue(isinstance(signed_msg_handlers[MESSAGE_DIGEST], Callable))
        self.assertTrue(isinstance(unsigned_msg_handlers[QUERY_DIGEST], Callable))
        self.assertTrue(QUERY_DIGEST in self.protocol.models)

    def test_protocol_to_include(self):
        self.agent.include(self.protocol)

        models = self.agent._models
        signed_msg_handlers = self.agent._signed_message_handlers
        unsigned_msg_handlers = self.agent._unsigned_message_handlers
        self.assertEqual(len(models), 2)
        self.assertEqual(len(unsigned_msg_handlers), 1)
        self.assertEqual(len(signed_msg_handlers), 1)
