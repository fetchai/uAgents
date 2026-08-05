import math
import unittest
from unittest.mock import AsyncMock, MagicMock

import pytest
from aioresponses import aioresponses
from cosmpy.aerial.tx import TxFee
from cosmpy.aerial.wallet import LocalWallet
from uagents_core.types import AgentEndpoint

from uagents.crypto import Identity
from uagents.network import get_ledger
from uagents.registration import (
    AgentRegistrationAttestation,
    AlmanacApiRegistrationPolicy,
    BatchLedgerRegistrationPolicy,
    DefaultBatchRegistrationPolicy,
    DefaultRegistrationPolicy,
    LedgerBasedRegistrationPolicy,
    coerce_metadata_to_str,
    copy_tx_fee,
)

TEST_PROTOCOLS = ["foo", "bar", "baz"]
TEST_ENDPOINTS = [
    AgentEndpoint(url="https://foobar.com", weight=1),
    AgentEndpoint(url="https://barbaz.com", weight=1),
]
TEST_FEE_AMOUNT = "1000atestfet"
# afet per unit of gas that fetchhub-4 validators are asked to require, per FIP discussion #8
FETCHHUB_MINIMUM_GAS_PRICE_FLOOR = 2


def test_attestation_signature():
    identity = Identity.generate()

    # create a dummy attestation
    attestation = AgentRegistrationAttestation(
        agent_identifier=identity.address,
        protocols=TEST_PROTOCOLS,
        endpoints=TEST_ENDPOINTS,
    )

    # sign the attestation with the identity
    attestation.sign(identity)
    assert attestation.signature is not None

    # verify the attestation
    assert attestation.verify()


def test_attestation_signature_with_metadata():
    identity = Identity.generate()

    # create a dummy attestation
    attestation = AgentRegistrationAttestation(
        agent_identifier=identity.address,
        protocols=TEST_PROTOCOLS,
        endpoints=TEST_ENDPOINTS,
        metadata=coerce_metadata_to_str(
            {
                "foo": "bar",
                "baz": 3.17,
                "qux": {"a": "b", "c": 4, "d": 5.6},
                "quux": ["corge", "grault", 2],
            }
        ),
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
        agent_identifier=identity.address,
        protocols=TEST_PROTOCOLS,
        endpoints=TEST_ENDPOINTS,
    )
    original_attestation.sign(identity)

    # recover the attestation
    recovered = AgentRegistrationAttestation(
        agent_identifier=original_attestation.agent_identifier,
        protocols=TEST_PROTOCOLS,
        endpoints=TEST_ENDPOINTS,
        signature=original_attestation.signature,
        timestamp=original_attestation.timestamp,
    )
    assert recovered.verify()


@pytest.fixture
def granter_address():
    return LocalWallet.generate().address()


@pytest.fixture
def almanac_contract():
    contract = MagicMock()
    contract.get_registration_fee.return_value = 0
    contract.is_registered.return_value = False
    contract.register = AsyncMock()
    contract.register_batch = AsyncMock()
    return contract


@pytest.fixture
def ledger():
    client = MagicMock()
    client.query_bank_balance.return_value = 10**20
    return client


def test_every_network_has_a_gas_price_that_scales_the_registration_fee():
    for network, denomination in (("mainnet", "afet"), ("testnet", "atestfet")):
        ledger = get_ledger(network)
        gas_price = ledger.network_config.fee_minimum_gas_price

        # a zero gas price yields a zero fee, which validators reject
        assert gas_price > 0
        assert ledger.estimate_fee_from_gas(200_000) == (
            f"{math.ceil(gas_price * 200_000)}{denomination}"
        )


def test_mainnet_gas_price_meets_the_network_minimum():
    mainnet = get_ledger("mainnet")

    assert mainnet.network_config.chain_id == "fetchhub-4"
    assert (
        mainnet.network_config.fee_minimum_gas_price >= FETCHHUB_MINIMUM_GAS_PRICE_FLOOR
    )


def test_copy_tx_fee_of_none_is_none():
    assert copy_tx_fee(None) is None


def test_copy_tx_fee_preserves_fields_without_sharing_state(granter_address):
    original = TxFee(amount=TEST_FEE_AMOUNT, gas_limit=200_000, granter=granter_address)

    copied = copy_tx_fee(original)

    assert copied is not original
    assert str(copied.amount) == str(original.amount)
    assert copied.gas_limit == original.gas_limit
    assert copied.granter == granter_address

    # cosmpy fills these in on the instance it is given; the original must not be affected
    copied.gas_limit = 300_000
    copied.amount = "1atestfet"
    assert original.gas_limit == 200_000
    assert str(original.amount) == TEST_FEE_AMOUNT


@pytest.mark.asyncio
async def test_ledger_policy_sends_a_copy_of_the_fee(
    ledger, almanac_contract, granter_address
):
    tx_fee = TxFee(amount=TEST_FEE_AMOUNT, granter=granter_address)
    identity = Identity.generate()
    policy = LedgerBasedRegistrationPolicy(
        ledger,
        LocalWallet.generate(),
        almanac_contract,
        testnet=True,
        tx_fee=tx_fee,
    )

    await policy.register(
        agent_identifier=identity.address,
        identity=identity,
        protocols=TEST_PROTOCOLS,
        endpoints=TEST_ENDPOINTS,
    )

    sent_fee = almanac_contract.register.await_args.kwargs["tx_fee"]
    assert sent_fee is not tx_fee
    assert sent_fee.granter == granter_address
    assert str(sent_fee.amount) == TEST_FEE_AMOUNT


@pytest.mark.asyncio
async def test_batch_ledger_policy_sends_a_copy_of_the_fee(
    ledger, almanac_contract, granter_address
):
    tx_fee = TxFee(amount=TEST_FEE_AMOUNT, granter=granter_address)
    policy = BatchLedgerRegistrationPolicy(
        ledger,
        LocalWallet.generate(),
        almanac_contract,
        testnet=True,
        tx_fee=tx_fee,
    )

    await policy.register()

    sent_fee = almanac_contract.register_batch.await_args.kwargs["tx_fee"]
    assert sent_fee is not tx_fee
    assert sent_fee.granter == granter_address
    assert str(sent_fee.amount) == TEST_FEE_AMOUNT


def test_default_policy_forwards_the_fee_to_the_ledger_policy(
    ledger, almanac_contract, granter_address
):
    tx_fee = TxFee(granter=granter_address)

    policy = DefaultRegistrationPolicy(
        ledger, LocalWallet.generate(), almanac_contract, testnet=True, tx_fee=tx_fee
    )

    assert policy._ledger_policy is not None
    assert policy._ledger_policy._tx_fee is tx_fee


def test_default_batch_policy_forwards_the_fee_to_the_ledger_policy(
    ledger, almanac_contract, granter_address
):
    tx_fee = TxFee(granter=granter_address)

    policy = DefaultBatchRegistrationPolicy(
        ledger, LocalWallet.generate(), almanac_contract, testnet=True, tx_fee=tx_fee
    )

    assert policy._ledger_policy is not None
    assert policy._ledger_policy._tx_fee is tx_fee


class TestContextSendMethods(unittest.IsolatedAsyncioTestCase):
    # we use a mocked almanac API uri
    MOCKED_ALMANAC_API = "http://127.0.0.1:8888/v1/almanac"

    def setUp(self):
        self.identity = Identity.generate()
        self.policy = AlmanacApiRegistrationPolicy(
            almanac_api=self.MOCKED_ALMANAC_API, max_retries=1
        )

    @aioresponses()
    async def test_registration_success(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(f"{self.MOCKED_ALMANAC_API}/agents", status=200)

        await self.policy.register(
            agent_identifier=self.identity.address,
            identity=self.identity,
            protocols=TEST_PROTOCOLS,
            endpoints=TEST_ENDPOINTS,
        )
        self.assertIsNotNone(self.policy.last_successful_registration)

    @aioresponses()
    async def test_registration_failure(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(f"{self.MOCKED_ALMANAC_API}/agents", status=400)

        await self.policy.register(
            agent_identifier=self.identity.address,
            identity=self.identity,
            protocols=TEST_PROTOCOLS,
            endpoints=TEST_ENDPOINTS,
        )
        self.assertIsNone(self.policy.last_successful_registration)

    @aioresponses()
    async def test_registration_server_failure(self, mocked_responses):
        # Mock the HTTP POST request with a status code and response content
        mocked_responses.post(f"{self.MOCKED_ALMANAC_API}/agents", status=500)

        await self.policy.register(
            agent_identifier=self.identity.address,
            identity=self.identity,
            protocols=TEST_PROTOCOLS,
            endpoints=TEST_ENDPOINTS,
        )
        self.assertIsNone(self.policy.last_successful_registration)
