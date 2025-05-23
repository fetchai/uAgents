# pylint: disable=protected-access
import unittest
from collections.abc import Callable

from uagents import Agent, Context, Model
from uagents.resolver import GlobalResolver
from uagents.types import RestHandlerDetails


class Message(Model):
    message: str


class Query(Model):
    query: str


class Response(Model):
    response: str


MESSAGE_DIGEST = Model.build_schema_digest(Message)
QUERY_DIGEST = Model.build_schema_digest(Query)


alice = Agent(
    name="alice", seed="alice recovery password", enable_agent_inspector=False
)


class TestAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = alice
        return super().setUp()

    def test_agent_init(self):
        self.assertIsNotNone(self.agent._wallet)
        self.assertIsNotNone(self.agent._identity)
        self.assertIsNotNone(self.agent._server)
        self.assertTrue(self.agent._dispatcher.contains(self.agent.address))
        self.assertTrue(isinstance(self.agent._resolver, GlobalResolver))

    def test_agent_on_interval(self):
        @self.agent.on_interval(period=10)
        def _(_ctx: Context):
            pass

        interval = self.agent._protocol._interval_handlers[0]
        self.assertTrue(isinstance(interval[0], Callable))
        self.assertEqual(interval[1], 10)

    def test_agent_on_signed_message(self):
        @self.agent.on_message(Message)
        def _(_ctx: Context, _sender: str, _msg: Message):
            pass

        signed_msg_handlers = self.agent._protocol._signed_message_handlers
        unsigned_msg_handlers = self.agent._protocol._unsigned_message_handlers

        self.assertEqual(len(unsigned_msg_handlers), 0)
        self.assertEqual(len(signed_msg_handlers), 2)
        self.assertTrue(isinstance(signed_msg_handlers[MESSAGE_DIGEST], Callable))

    def test_agent_on_unsigned_message(self):
        @self.agent.on_message(Query, allow_unverified=True)
        def _(_ctx: Context, _sender: str, _msg: Query):
            pass

        signed_msg_handlers = self.agent._protocol._signed_message_handlers
        unsigned_msg_handlers = self.agent._protocol._unsigned_message_handlers

        self.assertEqual(len(unsigned_msg_handlers), 1)
        self.assertEqual(len(signed_msg_handlers), 2)
        self.assertTrue(isinstance(signed_msg_handlers[MESSAGE_DIGEST], Callable))
        self.assertTrue(isinstance(unsigned_msg_handlers[QUERY_DIGEST], Callable))

    def test_agent_on_startup_event(self):
        @self.agent.on_event("startup")
        def _(ctx: Context):
            ctx.storage.set("startup", True)

        startup_handlers = self.agent._on_startup
        self.assertEqual(len(startup_handlers), 1)
        self.assertTrue(isinstance(startup_handlers[0], Callable))
        self.assertIsNone(self.agent._storage.get("startup"))

    def test_agent_on_shutdown_event(self):
        @self.agent.on_event("shutdown")
        def _(ctx: Context):
            ctx.storage.set("startup", True)

        shutdown_handlers = self.agent._on_shutdown
        self.assertEqual(len(shutdown_handlers), 1)
        self.assertTrue(isinstance(shutdown_handlers[0], Callable))
        self.assertIsNone(self.agent._storage.get("shutdown"))

    def test_agent_on_rest_get(self):
        @self.agent.on_rest_get("/get", Response)
        def _(_ctx: Context):
            return {}

        rest_handlers = self.agent._server._rest_handler_map
        get_handlers = [
            handler for handler in rest_handlers.values() if handler.method == "GET"
        ]
        self.assertEqual(len(get_handlers), 1)

        handler = rest_handlers[(self.agent.address, "GET", "/get")]
        self.assertTrue(isinstance(handler, RestHandlerDetails))
        self.assertEqual(handler.method, "GET")
        self.assertIsNone(handler.request_model)
        self.assertEqual(handler.response_model, Response)

    def test_agent_on_rest_post(self):
        @self.agent.on_rest_post("/post", Message, Response)
        def _(_ctx: Context, _req: Message):
            return Response(response="test")

        rest_handlers = self.agent._server._rest_handler_map
        post_handlers = [
            handler for handler in rest_handlers.values() if handler.method == "POST"
        ]
        self.assertEqual(len(post_handlers), 1)

        handler = rest_handlers[(self.agent.address, "POST", "/post")]
        self.assertTrue(isinstance(handler, RestHandlerDetails))
        self.assertEqual(handler.method, "POST")
        self.assertEqual(handler.request_model, Message)
        self.assertEqual(handler.response_model, Response)
