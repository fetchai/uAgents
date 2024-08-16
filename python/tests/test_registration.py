import unittest

import pytest
from aiohttp import ClientResponseError
from aioresponses import aioresponses

from uagents.crypto import Identity
from uagents.registration import (
    AgentRegistrationAttestation,
    AlmanacApiRegistrationPolicy,
)


def test_attestation_signature():
    identity = Identity.generate()

    # create a dummy attestation
    attestation = AgentRegistrationAttestation(
        agent_address=identity.address,
        protocols=["foo", "bar", "baz"],
        endpoints=[
            {"url": "https://foobar.com", "weight": 1},
            {"url": "https://barbaz.com", "weight": 1},
        ],
    )

    # sign the attestation with the identity
    attestation.sign(identity)
    assert attestation.signature is not None

    # verify the attestation
    assert attestation.verify()


def test_recovery_of_attestation():
    identity = Identity.generate()

    # create an attestation
    original_attestation = AgentRegistrationAttestation(
        agent_address=identity.address,
        protocols=["foo", "bar", "baz"],
        endpoints=[
            {"url": "https://foobar.com", "weight": 1},
            {"url": "https://barbaz.com", "weight": 1},
        ],
    )
    original_attestation.sign(identity)

    # recover the attestation
    recovered = AgentRegistrationAttestation(
        agent_address=original_attestation.agent_address,
        protocols=["foo", "bar", "baz"],
        endpoints=[
            {"url": "https://foobar.com", "weight": 1},
            {"url": "https://barbaz.com", "weight": 1},
        ],
        signature=original_attestation.signature,
    )
    assert recovered.verify()


def test_order_of_protocols_or_endpoints_does_not_matter():
    identity = Identity.generate()

    # create an attestation
    original_attestation = AgentRegistrationAttestation(
        agent_address=identity.address,
        protocols=["foo", "bar", "baz"],
        endpoints=[
            {"url": "https://foobar.com", "weight": 1},
            {"url": "https://barbaz.com", "weight": 1},
        ],
    )
    original_attestation.sign(identity)

    # recover the attestation
    recovered = AgentRegistrationAttestation(
        agent_address=original_attestation.agent_address,
        protocols=["baz", "foo", "bar"],
        endpoints=[
            {"url": "https://barbaz.com", "weight": 1},
            {"url": "https://foobar.com", "weight": 1},
        ],
        signature=original_attestation.signature,
    )
    assert recovered.verify()


class TestContextSendMethods(unittest.IsolatedAsyncioTestCase):
    # we use a mocked almanac API uri
    MOCKED_ALMANAC_API = "http://127.0.0.1:8888/v1/almanac"

    def setUp(self):
        self.identity = Identity.generate()
        self.policy = AlmanacApiRegistrationPolicy(
            self.identity, almanac_api=self.MOCKED_ALMANAC_API
        )

    @aioresponses()
    async def test_registration_success(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(f"{self.MOCKED_ALMANAC_API}/agents", status=200)

        await self.policy.register(
            agent_address=self.identity.address,
            protocols=["foo", "bar", "baz"],
            endpoints=[
                {"url": "https://foobar.com", "weight": 1},
                {"url": "https://barbaz.com", "weight": 1},
            ],
        )

    @aioresponses()
    async def test_registration_failure(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(f"{self.MOCKED_ALMANAC_API}/agents", status=400)

        with pytest.raises(ClientResponseError):
            await self.policy.register(
                agent_address=self.identity.address,
                protocols=["foo", "bar", "baz"],
                endpoints=[
                    {"url": "https://foobar.com", "weight": 1},
                    {"url": "https://barbaz.com", "weight": 1},
                ],
            )

    @aioresponses()
    async def test_registration_server_failure(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(f"{self.MOCKED_ALMANAC_API}/agents", status=500)

        with pytest.raises(ClientResponseError):
            await self.policy.register(
                agent_address=self.identity.address,
                protocols=["foo", "bar", "baz"],
                endpoints=[
                    {"url": "https://foobar.com", "weight": 1},
                    {"url": "https://barbaz.com", "weight": 1},
                ],
            )
