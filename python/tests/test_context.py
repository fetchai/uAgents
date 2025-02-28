# pylint: disable=protected-access
import asyncio
import unittest
from typing import Dict, Optional

from aioresponses import aioresponses

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
from uagents.envelope import Envelope
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
        replies: Optional[Dict[str, Dict[str, type[Model]]]] = None,
        queries: Optional[Dict[str, asyncio.Future]] = None,
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
            message_received=MsgInfo(message=message, sender=sender, schema_digest=schema_digest),
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
        env.sign(self.clyde._identity.sign_digest)
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
        env.sign(self.clyde._identity.sign_digest)
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
