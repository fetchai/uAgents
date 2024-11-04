import asyncio
import unittest

from cosmpy.aerial.wallet import LocalWallet

from uagents import Agent, Bureau
from uagents.registration import (
    AgentEndpoint,
    BatchLedgerRegistrationPolicy,
    DefaultBatchRegistrationPolicy,
    DefaultRegistrationPolicy,
    LedgerBasedRegistrationPolicy,
)

ALICE_ENDPOINT = AgentEndpoint(url="http://alice:8000/submit", weight=1)
BOB_ENDPOINT = AgentEndpoint(url="http://bob:8000/submit", weight=1)
BUREAU_ENDPOINT = AgentEndpoint(url="http://bureau:8000/submit", weight=1)


bureau_wallet = LocalWallet.generate()


class TestBureau(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()
        return super().setUp()

    def test_bureau_updates_agents_no_ledger_batch(self):
        alice = Agent(name="alice", endpoint=ALICE_ENDPOINT.url, loop=self.loop)
        bob = Agent(name="bob", endpoint=BOB_ENDPOINT.url)

        assert alice._endpoints == [ALICE_ENDPOINT]
        assert bob._endpoints == [BOB_ENDPOINT]

        assert isinstance(alice._registration_policy, DefaultRegistrationPolicy)
        assert isinstance(bob._registration_policy, DefaultRegistrationPolicy)

        bureau = Bureau(agents=[alice, bob], endpoint=BUREAU_ENDPOINT.url)

        assert alice._endpoints == [BUREAU_ENDPOINT]
        assert bob._endpoints == [BUREAU_ENDPOINT]

        assert isinstance(bureau._registration_policy, DefaultBatchRegistrationPolicy)
        assert bureau._registration_policy._ledger_policy is None
        assert isinstance(alice._registration_policy, LedgerBasedRegistrationPolicy)
        assert isinstance(bob._registration_policy, LedgerBasedRegistrationPolicy)

    def test_bureau_updates_agents_with_wallet(self):
        alice = Agent(name="alice", endpoint=ALICE_ENDPOINT.url)
        bob = Agent(name="bob", endpoint=BOB_ENDPOINT.url)

        assert isinstance(alice._registration_policy, DefaultRegistrationPolicy)
        assert isinstance(bob._registration_policy, DefaultRegistrationPolicy)

        bureau = Bureau(agents=[alice, bob], wallet=bureau_wallet)

        assert alice._endpoints == []
        assert bob._endpoints == []

        assert isinstance(bureau._registration_policy, DefaultBatchRegistrationPolicy)
        assert isinstance(
            bureau._registration_policy._ledger_policy, BatchLedgerRegistrationPolicy
        )
        assert alice._registration_policy is None
        assert bob._registration_policy is None

    def test_bureau_updates_agents_with_seed(self):
        alice = Agent(name="alice", endpoint=ALICE_ENDPOINT.url)
        bob = Agent(name="bob", endpoint=BOB_ENDPOINT.url)

        assert isinstance(alice._registration_policy, DefaultRegistrationPolicy)
        assert isinstance(bob._registration_policy, DefaultRegistrationPolicy)

        bureau = Bureau(
            agents=[alice, bob],
            endpoint=BUREAU_ENDPOINT.url,
            seed="bureau test seed phrase",
        )

        assert isinstance(bureau._registration_policy, DefaultBatchRegistrationPolicy)
        assert isinstance(
            bureau._registration_policy._ledger_policy, BatchLedgerRegistrationPolicy
        )
        assert alice._registration_policy is None
        assert bob._registration_policy is None

    def test_bureau_updates_agents_wallet_overrides_seed(self):
        alice = Agent(name="alice", endpoint=ALICE_ENDPOINT.url)
        bob = Agent(name="bob", endpoint=BOB_ENDPOINT.url)

        assert isinstance(alice._registration_policy, DefaultRegistrationPolicy)
        assert isinstance(bob._registration_policy, DefaultRegistrationPolicy)

        bureau = Bureau(
            agents=[alice, bob],
            endpoint=BUREAU_ENDPOINT.url,
            wallet=bureau_wallet,
            seed="bureau test seed phrase",
        )

        assert isinstance(bureau._registration_policy, DefaultBatchRegistrationPolicy)
        assert isinstance(
            bureau._registration_policy._ledger_policy, BatchLedgerRegistrationPolicy
        )
        assert (
            bureau._registration_policy._ledger_policy._wallet.address()
            == bureau_wallet.address()
        )
        assert alice._registration_policy is None
        assert bob._registration_policy is None
