# pylint: disable=protected-access
import asyncio
import unittest

from aioresponses import aioresponses
from uagents import Agent
from uagents.context import (
    DeliveryStatus,
    MsgDigest,
    MsgStatus,
    Identity,
    Model,
)
from uagents.dispatch import dispatcher
from uagents.resolver import RulesBasedResolver


class Incoming(Model):
    text: str


class Message(Model):
    message: str


endpoints = ["http://localhost:8000"]
clyde = Agent(name="clyde", seed="clyde recovery phrase", endpoint=endpoints)
dispatcher.unregister(clyde.address, clyde)
resolver = RulesBasedResolver(
    rules={
        clyde.address: endpoints,
    }
)
alice = Agent(name="alice", seed="alice recovery phrase", resolve=resolver)
bob = Agent(name="bob", seed="bob recovery phrase")
incoming = Incoming(text="hello")
incoming_digest = Model.build_schema_digest(incoming)
msg = Message(message="hey")
msg_digest = Model.build_schema_digest(msg)


class TestContextSendMethods(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = alice
        self.context = self.agent._ctx

    async def test_send_local_dispatch(self):
        result = await self.context.send(bob.address, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message dispatched locally",
            destination=bob.address,
            endpoint="",
        )

        self.assertEqual(result, exp_msg_status)

    async def test_send_local_dispatch_valid_reply(self):
        self.context._message_received = MsgDigest(
            message=incoming, schema_digest=incoming_digest
        )
        self.context._replies[incoming_digest] = {msg_digest: Message}
        result = await self.context.send(bob.address, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message dispatched locally",
            destination=bob.address,
            endpoint="",
        )

        self.assertEqual(result, exp_msg_status)
        self.context._message_received = None
        self.context._replies = {}

    async def test_send_local_dispatch_invalid_reply(self):
        self.context._message_received = MsgDigest(
            message=incoming, schema_digest=incoming_digest
        )
        self.context._replies[incoming_digest] = {msg_digest: Message}
        result = await self.context.send(bob.address, incoming)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Invalid reply",
            destination=bob.address,
            endpoint="",
        )

        self.assertEqual(result, exp_msg_status)
        self.context._message_received = None
        self.context._replies = {}

    async def test_send_local_dispatch_valid_interval_msg(self):
        self.context._interval_messages = {msg_digest}
        result = await self.context.send(bob.address, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message dispatched locally",
            destination=bob.address,
            endpoint="",
        )

        self.assertEqual(result, exp_msg_status)
        self.context._interval_messages = set()

    async def test_send_local_dispatch_invalid_interval_msg(self):
        self.context._interval_messages = {msg_digest}
        result = await self.context.send(bob.address, incoming)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Invalid interval message",
            destination=bob.address,
            endpoint="",
        )

        self.assertEqual(result, exp_msg_status)

    async def test_send_resolve_sync_query(self):
        future = asyncio.Future()
        self.context._queries[clyde.address] = future
        result = await self.context.send(clyde.address, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Sync message resolved",
            destination=clyde.address,
            endpoint="",
        )

        self.assertEqual(future.result(), (msg.json(), msg_digest))
        self.assertEqual(result, exp_msg_status)
        self.assertEqual(
            len(self.context._queries), 0, "Query not removed from context"
        )

    async def test_send_external_dispatch_resolve_failure(self):
        destination = Identity.generate().address
        result = await self.context.send(destination, msg)
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Unable to resolve destination endpoint",
            destination=destination,
            endpoint="",
        )

        self.assertEqual(result, exp_msg_status)

    @aioresponses()
    async def test_send_external_dispatch_success(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(endpoints[0], status=200)

        # Perform the actual operation
        result = await self.context.send(clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message successfully delivered via HTTP",
            destination=clyde.address,
            endpoint=endpoints[0],
        )

        # Assertions
        self.assertEqual(result, exp_msg_status)

    @aioresponses()
    async def test_send_external_dispatch_failure(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(endpoints[0], status=404)

        # Perform the actual operation
        result = await self.context.send(clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Message delivery failed",
            destination=clyde.address,
            endpoint="",
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

        # Perform the actual operation
        result = await self.context.send(clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message successfully delivered via HTTP",
            destination=clyde.address,
            endpoint=endpoints[0],
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

        # Perform the actual operation
        result = await self.context.send(clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.DELIVERED,
            detail="Message successfully delivered via HTTP",
            destination=clyde.address,
            endpoint=endpoints[1],
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

        # Perform the actual operation
        result = await self.context.send(clyde.address, msg)

        # Define the expected message status
        exp_msg_status = MsgStatus(
            status=DeliveryStatus.FAILED,
            detail="Message delivery failed",
            destination=clyde.address,
            endpoint="",
        )

        # Assertions
        self.assertEqual(result, exp_msg_status)

        endpoints.pop()
