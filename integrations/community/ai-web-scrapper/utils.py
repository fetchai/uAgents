import asyncio
import uuid
from typing import Type
from uagents import Agent, Context, Model
from uagents.context import DeliveryStatus
from uagents.envelope import Envelope
from uagents.resolver import GlobalResolver
from uagents.setup import fund_agent_if_low

class AgentAdapterError(Exception):
    pass


class AgentProtocolAdapter:
    def __init__(self, *, endpoint: str):
        agent_loop = asyncio.new_event_loop()

        self._timeout = 50
        self._poll_interval = 0.5
        self._poll_attempts = int(self._timeout / self._poll_interval)
        self.agent = Agent(
            seed=f"this is the agent multiplexer secret seed",
            endpoint=endpoint,
            loop=agent_loop,
        )
        self.resolver = GlobalResolver()
        self.response = None

        # ensure that our "agent" has enough balance to register on the testnet
        fund_agent_if_low(str(self.agent.wallet.address()))
        agent_loop.run_until_complete(self.agent.register())
        agent_loop.close()

    async def send_message(
        self,
        destination_address: str,
        message: Model
        # expected_response_type: Type[Model],
    ) -> Model:
        # generate a session id (to uniquely identify the exchange)
        self.response = None
        session_id = uuid.uuid4()

        # build and send the message to the agent
        result = await Context.send_raw_exchange_envelope(
            self.agent._identity,
            destination_address,
            self.resolver,
            Model.build_schema_digest(message),
            None,
            message.json(),
            session_id=session_id,
        )

        print("Delivery Response", result)

        # check if the message was sent successfully
        if result.status == DeliveryStatus.FAILED:
            raise AgentAdapterError("Failed to send message to agent")

        print("Session ID: " + str(session_id))
        # NOTE: you should just be able to `await response_future` here, but for some
        # reason Django has a problem with that. So we poll the future instead.

        response = None
        for _ in range(0, self._poll_attempts):
            try:
                print(self.response)
                if self.response is not None:
                    response = self.response
                    break

            except Exception as e:
                print(e, "exception")
            await asyncio.sleep(self._poll_interval)

        print("Agent Delivery Response, ", response)

        # check if we timed out our waiting for a response
        if self.response is None:
            raise AgentAdapterError("Timeout waiting for response")

        # parse the raw response
        return self.response


    def process_response(self, data: dict):
        # parse the raw envelope

        envelope = Envelope.parse_obj(data)

        # verify the signature
        if not envelope.verify():
            raise AgentAdapterError("Invalid signature")

        # get the session id
        session = str(envelope.session)

        # ensure that we are expecting a response for this session
        self.response = envelope.decode_payload()

        print(self.response)
        return {}