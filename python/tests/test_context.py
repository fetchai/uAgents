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
    MsgDigest,
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

        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.alice._dispenser.run())

    def get_external_context(
        self,
        message: Model,
        schema_digest: str,
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
            message_received=MsgDigest(message=message, schema_digest=schema_digest),
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
            incoming, incoming_digest, replies=test_replies
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
            incoming, incoming_digest, replies=test_replies
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
