# pylint: disable=protected-access
import asyncio
import unittest

from aioresponses import aioresponses
from uagents_core.envelope import Envelope

from uagents import Agent
from uagents.context import (
    DeliveryStatus,
    ExternalContext,
    Model,
    MsgInfo,
    MsgStatus,
)
from uagents.crypto import Identity
from uagents.dispatch import dispatcher
from uagents.resolver import RulesBasedResolver


class Incoming(Model):
    text: str


class Message(Model):
    message: str


endpoints = ["http://localhost:8000"]

incoming = Incoming(text="hello")
incoming_digest = Model.build_schema_digest(incoming)

msg = Message(message="hey")
msg_digest = Model.build_schema_digest(msg)
test_replies = {incoming_digest: {msg_digest: Message}}


class TestContextSendMethods(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # agents need to be recreated for each test
        self.clyde = Agent(
            name="clyde", seed="clyde recovery phrase", endpoint=endpoints
        )
        dispatcher.unregister(self.clyde.address, self.clyde)
        resolver = RulesBasedResolver(
            rules={
                self.clyde.address: endpoints,
            }
        )

        self.alice = Agent(name="alice", seed="alice recovery phrase", resolve=resolver)
        self.bob = Agent(name="bob", seed="bob recovery phrase")

        @self.bob.on_message(model=Message)
        async def _(ctx, sender, msg):
            await asyncio.sleep(1.1)
            await ctx.send(sender, incoming)

        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.alice._dispenser.run())
        self.bob.include(self.bob._protocol)
        self.loop.create_task(self.bob._process_message_queue())
        self.loop.create_task(self.bob._dispenser.run())

    def get_external_context(
        self,
        message: Model,
        schema_digest: str,
        sender: str,
        replies: dict[str, dict[str, type[Model]]] | None = None,
        queries: dict[str, asyncio.Future] | None = None,
    ):
        return ExternalContext(
            agent=self.alice,
            storage=self.alice._storage,
            ledger=self.alice._ledger,
            resolver=self.alice._resolver,
            dispenser=self.alice._dispenser,
            wallet_messaging_client=self.alice._wallet_messaging_client,
            logger=self.alice._logger,
            queries=queries,
            session=None,
            replies=replies,
            message_received=MsgInfo(
                message=message, sender=sender, schema_digest=schema_digest
            ),
        )

    async def test_send_local_dispatch(self):
        context = self.alice._build_context()
        result = await context.send(self.bob.address, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message dispatched locally",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        self.assertEqual(result, exp_msg_status)

    async def test_send_local_dispatch_valid_reply(self):
        context = self.get_external_context(
            incoming, incoming_digest, replies=test_replies, sender=self.bob.address
        )
        result = await context.send(self.bob.address, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message dispatched locally",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        self.assertEqual(result, exp_msg_status)

    async def test_send_local_dispatch_invalid_reply(self):
        context = self.get_external_context(
            incoming, incoming_digest, replies=test_replies, sender=self.bob.address
        )
        result = await context.send(self.bob.address, incoming)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Invalid reply",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        self.assertEqual(result, exp_msg_status)

    async def test_send_local_dispatch_not_a_reply(self):
        context = self.get_external_context(
            incoming, incoming_digest, replies=test_replies, sender=self.clyde.address
        )
        result = await context.send(self.bob.address, incoming)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message dispatched locally",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        self.assertEqual(result, exp_msg_status)

    async def test_send_local_dispatch_valid_interval_msg(self):
        context = self.alice._build_context()
        context._interval_messages = {msg_digest}
        result = await context.send(self.bob.address, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message dispatched locally",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        self.assertEqual(result, exp_msg_status)

    async def test_send_local_dispatch_invalid_interval_msg(self):
        context = self.alice._build_context()
        context._interval_messages = {msg_digest}
        result = await context.send(self.bob.address, incoming)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Invalid interval message",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        self.assertEqual(result, exp_msg_status)

    async def test_send_external_dispatch_resolve_failure(self):
        destination = Identity.generate().address
        context = self.alice._build_context()
        result = await context.send(destination, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Unable to resolve destination endpoint",
            destination=destination,
            endpoint="",
            session=context.session,
        )

        self.assertEqual(result, exp_msg_status)

    @aioresponses()
    async def test_send_external_dispatch_success(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(endpoints[0], status=200)

        context = self.alice._build_context()

        # Perform the actual operation
        result = await context.send(self.clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message successfully delivered via HTTP",
            destination=self.clyde.address,
            endpoint=endpoints[0],
            session=context.session,
        )

        # Assertions
        self.assertEqual(result, exp_msg_status)

    @aioresponses()
    async def test_send_external_dispatch_failure(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(endpoints[0], status=404)

        context = self.alice._build_context()

        # Perform the actual operation
        result = await context.send(self.clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Message delivery failed",
            destination=self.clyde.address,
            endpoint="",
            session=context.session,
        )

        # Assertions
        self.assertEqual(result, exp_msg_status)

    @aioresponses()
    async def test_send_external_dispatch_multiple_endpoints_first_success(
        self, mocked_responses
    ):
        endpoints.append("http://localhost:8001")

        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(endpoints[0], status=200)
        mocked_responses.post(endpoints[1], status=404)

        context = self.alice._build_context()

        # Perform the actual operation
        result = await context.send(self.clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message successfully delivered via HTTP",
            destination=self.clyde.address,
            endpoint=endpoints[0],
            session=context.session,
        )

        # Assertions
        self.assertEqual(result, exp_msg_status)

        # Ensure that only one request was sent
        mocked_responses.assert_called_once()

        endpoints.pop()

    @aioresponses()
    async def test_send_external_dispatch_multiple_endpoints_second_success(
        self, mocked_responses
    ):
        endpoints.append("http://localhost:8001")

        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(endpoints[0], status=404)
        mocked_responses.post(endpoints[1], status=200)

        context = self.alice._build_context()

        # Perform the actual operation
        result = await context.send(self.clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message successfully delivered via HTTP",
            destination=self.clyde.address,
            endpoint=endpoints[1],
            session=context.session,
        )

        # Assertions
        self.assertEqual(result, exp_msg_status)

        endpoints.pop()

    @aioresponses()
    async def test_send_external_dispatch_multiple_endpoints_failure(
        self, mocked_responses
    ):
        endpoints.append("http://localhost:8001")

        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(endpoints[0], status=404)
        mocked_responses.post(endpoints[1], status=404)

        context = self.alice._build_context()

        # Perform the actual operation
        result = await context.send(self.clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Message delivery failed",
            destination=self.clyde.address,
            endpoint="",
            session=context.session,
        )

        # Assertions
        self.assertEqual(result, exp_msg_status)

        endpoints.pop()

    @aioresponses()
    async def test_send_and_receive_sync_success(self, mocked_responses):
        context = self.alice._build_context()

        # Mock the HTTP POST request with a status code and response content
        env = Envelope(
            version=1,
            sender=self.clyde.address,
            target=self.alice.address,
            session=context.session,
            schema_digest=msg_digest,
        )
        env.encode_payload(incoming.model_dump_json())
        env.sign(self.clyde._identity)
        payload = env.model_dump()
        payload["session"] = str(env.session)
        mocked_responses.post(endpoints[0], status=200, payload=payload)

        # Perform the actual operation
        response, status = await context.send_and_receive(
            self.clyde.address, msg, response_type=Incoming, sync=True, timeout=5
        )

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Sync message successfully delivered via HTTP",
            destination=self.clyde.address,
            endpoint=endpoints[0],
            session=context.session,
        )

        # Assertions
        self.assertEqual(status, exp_msg_status)
        self.assertEqual(response, incoming)
        self.assertEqual(len(dispatcher.pending_responses), 0)

    @aioresponses()
    async def test_send_and_receive_sync_delivery_failure(self, mocked_responses):
        context = self.alice._build_context()

        # Mock the HTTP POST request with a status code and response content
        env = Envelope(
            version=1,
            sender=self.clyde.address,
            target=self.alice.address,
            session=context.session,
            schema_digest=msg_digest,
        )
        env.encode_payload(incoming.model_dump_json())
        env.sign(self.clyde._identity)
        payload = env.model_dump()
        payload["session"] = str(env.session)
        mocked_responses.post(endpoints[0], status=200, payload=payload)

        # Perform the actual operation
        _, status = await context.send_and_receive(
            self.clyde.address, msg, response_type=Incoming, sync=True, timeout=0
        )

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Timeout waiting for response",
            destination=self.clyde.address,
            endpoint="",
            session=context.session,
        )

        # Assertions
        self.assertEqual(status, exp_msg_status)
        self.assertEqual(len(dispatcher.pending_responses), 0)

    async def test_send_and_receive_async_success(self):
        context = self.alice._build_context()

        # Perform the actual operation
        response, status = await context.send_and_receive(
            self.bob.address, msg, response_type=Incoming, timeout=5
        )

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message dispatched locally",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        # Assertions
        self.assertEqual(status, exp_msg_status)
        self.assertEqual(response, incoming)
        self.assertEqual(len(dispatcher.pending_responses), 0)

    async def test_send_and_receive_async_timeout(self):
        context = self.alice._build_context()

        # Perform the actual operation
        _, status = await context.send_and_receive(
            self.bob.address, msg, response_type=Incoming, timeout=1
        )

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Timeout waiting for response",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        # Assertions
        self.assertEqual(status, exp_msg_status)
        self.assertEqual(len(dispatcher.pending_responses), 0)

    async def test_send_and_receive_async_wrong_response_type(self):
        context = self.alice._build_context()

        class WrongMessage(Model):
            wrong: str

        # Perform the actual operation
        response, status = await context.send_and_receive(
            self.bob.address, msg, response_type=WrongMessage, timeout=5
        )

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Received unexpected response type",
            destination=self.bob.address,
            endpoint="",
            session=context.session,
        )

        # Assertions
        self.assertEqual(status, exp_msg_status)
        self.assertEqual(len(dispatcher.pending_responses), 0)


class TestMessageHistory(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.alice = Agent(name="alice", seed="alice msg recovery phrase")
        self.bob_cache = Agent(
            name="bob", seed="bob cache recovery phrase", enable_agent_inspector=True
        )
        self.bob_store = Agent(
            enable_agent_inspector=False,
            store_message_history=True,
        )
        self.bob_both = Agent(
            store_message_history=True,
            enable_agent_inspector=True,
        )
        self.bob_neither = Agent(enable_agent_inspector=False)
        self.bob_retention_period = Agent(
            store_message_history=True,
            enable_agent_inspector=True,
        )
        assert self.bob_retention_period._message_history is not None
        self.bob_retention_period._message_history._retention_period = 1
        self.bob_message_limit = Agent(
            store_message_history=True,
            enable_agent_inspector=True,
        )
        assert self.bob_message_limit._message_history is not None
        self.bob_message_limit._message_history._message_limit = 2

        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.alice._dispenser.run())
        for bob in [
            self.bob_cache,
            self.bob_store,
            self.bob_both,
            self.bob_neither,
            self.bob_retention_period,
            self.bob_message_limit,
        ]:

            @bob.on_message(Message)
            async def _(ctx, sender, _msg):
                await ctx.send(sender, incoming)

            bob.include(bob._protocol)
            self.loop.create_task(bob._process_message_queue())
            self.loop.create_task(bob._dispenser.run())

    async def test_messages_cached_not_stored(self):
        ctx = self.alice._build_context()
        await ctx.send(self.bob_cache.address, msg)
        await asyncio.sleep(0.1)

        message_history = self.bob_cache._message_history
        assert message_history is not None
        msgs = message_history.get_cached_messages().envelopes
        self.assertEqual(len(msgs), 2)

        with self.assertRaises(ValueError):
            _ = message_history.get_session_messages(ctx.session)

    async def test_messages_stored_not_cached(self):
        ctx = self.alice._build_context()
        await ctx.send(self.bob_store.address, msg)
        await asyncio.sleep(0.1)

        message_history = self.bob_store._message_history
        assert message_history is not None
        with self.assertRaises(ValueError):
            _ = message_history.get_cached_messages()

        stored_msgs = message_history.get_session_messages(ctx.session)
        self.assertEqual(len(stored_msgs), 2)

    async def test_messages_stored_and_cached(self):
        ctx = self.alice._build_context()
        await ctx.send(self.bob_both.address, msg)
        await asyncio.sleep(0.1)

        message_history = self.bob_both._message_history
        assert message_history is not None
        msgs = message_history.get_cached_messages().envelopes
        self.assertEqual(len(msgs), 2)

        stored_msgs = message_history.get_session_messages(ctx.session)
        self.assertEqual(len(stored_msgs), 2)

    async def test_messages_neither_stored_nor_cached(self):
        ctx = self.alice._build_context()
        await ctx.send(self.bob_neither.address, msg)
        await asyncio.sleep(0.1)

        message_history = self.bob_neither._message_history
        assert message_history is None

        key = f"message-history:session:{str(ctx.session)}"
        messages = self.bob_neither.storage.get(key) or []
        self.assertEqual(len(messages), 0)

    async def test_messages_deleted_after_retention_period(self):
        ctx = self.alice._build_context()
        await ctx.send(self.bob_retention_period.address, msg)
        await asyncio.sleep(0.1)

        message_history = self.bob_retention_period._message_history
        assert message_history is not None
        msgs = message_history.get_cached_messages().envelopes
        self.assertEqual(len(msgs), 2)

        stored_msgs = message_history.get_session_messages(ctx.session)
        self.assertEqual(len(stored_msgs), 2)

        await asyncio.sleep(1)
        await ctx.send(self.bob_retention_period.address, msg)
        await asyncio.sleep(0.1)

        msgs = message_history.get_cached_messages().envelopes

        # The first 2 messages should be deleted from cache, leaving only the second 2
        self.assertEqual(len(msgs), 2)

        # All messages should still be in storage since session is still active
        stored_msgs = message_history.get_session_messages(ctx.session)
        self.assertEqual(len(stored_msgs), 4)

        await asyncio.sleep(1)
        message_history.apply_retention_policy()
        stored_msgs = message_history.get_session_messages(ctx.session)

        # All messages should now be deleted from storage since last message is older
        # than retention period
        self.assertEqual(len(stored_msgs), 0)

    async def test_message_storage_blocked_after_limit_reached(self):
        ctx = self.alice._build_context()
        await ctx.send(self.bob_message_limit.address, msg)
        await asyncio.sleep(0.1)

        message_history = self.bob_message_limit._message_history
        assert message_history is not None
        msgs = message_history.get_cached_messages().envelopes
        self.assertEqual(len(msgs), 2)

        stored_msgs = message_history.get_session_messages(ctx.session)
        self.assertEqual(len(stored_msgs), 2)

        await ctx.send(self.bob_message_limit.address, msg)
        await asyncio.sleep(0.1)

        msgs = message_history.get_cached_messages().envelopes
        self.assertEqual(len(msgs), 2)

        stored_msgs = message_history.get_session_messages(ctx.session)
        self.assertEqual(len(stored_msgs), 2)
