import json
import logging
import unittest
from typing import Optional, Tuple

import grpc
from cosmpy.aerial.client import Account
from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.exceptions import BroadcastError
from cosmpy.aerial.tx import Transaction
from cosmpy.aerial.tx_helpers import SubmittedTx, TxResponse
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.address import Address
from cosmpy.protos.cosmwasm.wasm.v1.query_pb2 import QuerySmartContractStateRequest, QuerySmartContractStateResponse

from uagents.config import ALMANAC_CONTRACT_VERSION, REGISTRATION_FEE, TESTNET_CONTRACT_ALMANAC
from uagents.crypto import Identity
from uagents.network import AlmanacContract
from uagents.registration import LedgerBasedRegistrationPolicy, BatchLedgerRegistrationPolicy
from uagents.types import AgentInfo


class FakeSubmittedTx:
    def __init__(self):
        self.tx_hash = 'not-a-real-tx-hash'


class FakeTxResponse:
    def __init__(self):
        self.code = 0


def zero_retry_delay(index: int) -> float:
    return 0.0


class FakeWasmClient:
    def SmartContractState(self, req: QuerySmartContractStateRequest):
        data = json.loads(req.query_data)
        if data == {"query_contract_state": {}}:
            return QuerySmartContractStateResponse(
                data=json.dumps({'contract_version': ALMANAC_CONTRACT_VERSION}).encode()
            )
        elif 'query_records' in data:
            return QuerySmartContractStateResponse(
                data=json.dumps({}).encode()
            )
        print('Unknown request', req, data)
        assert False, "Unknown request"


class FakeLedgerClient:
    def __init__(self):
        self.wasm = FakeWasmClient()
        self.network_config = NetworkConfig.fetchai_mainnet()

        self._broadcast_failure_count = 0
        self._rpc_query_failure_count = 0
        self._query_failure_count = 0

    @property
    def broadcast_failure_count(self) -> int:
        return self._broadcast_failure_count

    @broadcast_failure_count.setter
    def broadcast_failure_count(self, value: int):
        self._broadcast_failure_count = value

    @property
    def rpc_query_failure_count(self) -> int:
        return self._rpc_query_failure_count

    @rpc_query_failure_count.setter
    def rpc_query_failure_count(self, value: int):
        self._rpc_query_failure_count = value

    @property
    def query_failure_count(self) -> int:
        return self._query_failure_count

    @query_failure_count.setter
    def query_failure_count(self, value: int):
        self._query_failure_count = value

    def query_bank_balance(self, address: Address, denom: Optional[str] = None) -> int:
        return REGISTRATION_FEE + 1

    def query_account(self, address: Address) -> Account:
        return Account(
            address=address,
            number=0,
            sequence=0,
        )

    def estimate_gas_and_fee_for_tx(self, tx: Transaction) -> Tuple[int, str]:
        return 0, f'0{self.network_config.fee_denomination}'

    def broadcast_tx(self, tx: Transaction) -> SubmittedTx:
        if self._broadcast_failure_count > 0:
            self._broadcast_failure_count -= 1
            print('Broadcast failure', self._broadcast_failure_count)
            raise BroadcastError('not-a-real-hash', 'not-a-real-tx-log')
        return FakeSubmittedTx()

    def query_tx(self, tx_hash: str) -> TxResponse:
        if self._query_failure_count > 0:
            self._query_failure_count -= 1
            print('Query failure', self._query_failure_count)
            raise RuntimeError('not-a-real-error')

        if self._rpc_query_failure_count > 0:
            self._rpc_query_failure_count -= 1
            print('RPC query failure', self._rpc_query_failure_count)
            raise grpc.RpcError('not-a-real-rpc-error')

        return FakeTxResponse()


class FlakeyNetworkRegistrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.wallet = LocalWallet.from_unsafe_seed("testing wallet")
        self.identity = Identity.from_seed("testing seeed", 1)

        self.ledger = FakeLedgerClient()
        self.contract = AlmanacContract(None, self.ledger, Address(TESTNET_CONTRACT_ALMANAC))

        self.logger = logging.getLogger('flakey')
        self.policy = LedgerBasedRegistrationPolicy(self.ledger, self.wallet, self.contract, True, logger=self.logger)

    async def test_happy_registration_path(self):
        await self.policy.register(self.identity.address, self.identity, [], [])

    async def test_retry_on_broadcast_failure(self):
        # configure the ledger to fail the first broadcast
        self.ledger.broadcast_failure_count = 8

        # configure the policy to retry once with a zero delay
        self.policy.broadcast_retries = 10
        self.policy.broadcast_retry_delay = zero_retry_delay

        await self.policy.register(
            self.identity.address,
            self.identity,
            [],
            [],
        )

        self.assertEqual(self.ledger.broadcast_failure_count, 0)
        self.assertIsNotNone(self.policy.last_successful_registration)

    async def test_retry_on_broadcast_failure_ultimately_failing(self):
        # configure the ledger to fail the first broadcast
        self.ledger.broadcast_failure_count = 12

        # configure the policy to retry once with a zero delay
        self.policy.broadcast_retries = 10
        self.policy.broadcast_retry_delay = zero_retry_delay

        await self.policy.register(
            self.identity.address,
            self.identity,
            [],
            [],
        )

        self.assertEqual(self.ledger.broadcast_failure_count, 2)
        self.assertIsNone(self.policy.last_successful_registration)

    async def test_retry_on_rpc_poll_failure_succeeds(self):
        # configure the ledger to fail the first broadcast
        self.ledger.rpc_query_failure_count = 4

        # configure the policy to retry once with a zero delay
        self.policy.poll_retries = 5
        self.policy.poll_retry_delay = zero_retry_delay

        await self.policy.register(
            self.identity.address,
            self.identity,
            [],
            [],
        )

        self.assertEqual(self.ledger.rpc_query_failure_count, 0)
        self.assertIsNotNone(self.policy.last_successful_registration)

    async def test_retry_on_rpc_poll_failure_fails(self):
        # configure the ledger to fail the first broadcast
        self.ledger.rpc_query_failure_count = 6

        # configure the policy to retry once with a zero delay
        self.policy.poll_retries = 5
        self.policy.poll_retry_delay = zero_retry_delay

        await self.policy.register(
            self.identity.address,
            self.identity,
            [],
            [],
        )

        self.assertEqual(self.ledger.rpc_query_failure_count, 1)
        self.assertIsNone(self.policy.last_successful_registration)


    async def test_retry_on_poll_failure_succeeds(self):
        # configure the ledger to fail the first broadcast
        self.ledger.query_failure_count = 4

        # configure the policy to retry once with a zero delay
        self.policy.poll_retries = 5
        self.policy.poll_retry_delay = zero_retry_delay

        await self.policy.register(
            self.identity.address,
            self.identity,
            [],
            [],
        )

        self.assertEqual(self.ledger.query_failure_count, 0)
        self.assertIsNotNone(self.policy.last_successful_registration)

    async def test_retry_on_poll_failure_fails(self):
        # configure the ledger to fail the first broadcast
        self.ledger.query_failure_count = 6

        # configure the policy to retry once with a zero delay
        self.policy.poll_retries = 5
        self.policy.poll_retry_delay = zero_retry_delay

        await self.policy.register(
            self.identity.address,
            self.identity,
            [],
            [],
        )

        self.assertEqual(self.ledger.query_failure_count, 1)
        self.assertIsNone(self.policy.last_successful_registration)


class FlakeyBatchNetworkRegistrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.wallet = LocalWallet.from_unsafe_seed("testing wallet")
        self.identity = Identity.from_seed("testing seeed", 1)

        self.ledger = FakeLedgerClient()
        self.contract = AlmanacContract(None, self.ledger, Address(TESTNET_CONTRACT_ALMANAC))

        self.logger = logging.getLogger('flakey')
        self.policy = BatchLedgerRegistrationPolicy(self.ledger, self.wallet, self.contract, True, logger=self.logger)

        info = AgentInfo(
            address=self.identity.address,
            prefix='test-agent',
            endpoints=[],
            protocols=[],
            metadata={},
        )
        self.policy.add_agent(info, self.identity)

    async def test_happy_registration_path(self):
        await self.policy.register()

    async def test_retry_on_broadcast_failure(self):
        # configure the ledger to fail the first broadcast
        self.ledger.broadcast_failure_count = 8

        # configure the policy to retry once with a zero delay
        self.policy.broadcast_retries = 10
        self.policy.broadcast_retry_delay = zero_retry_delay

        await self.policy.register()

        self.assertEqual(self.ledger.broadcast_failure_count, 0)
        self.assertIsNotNone(self.policy.last_successful_registration)

    async def test_retry_on_broadcast_failure_ultimately_failing(self):
        # configure the ledger to fail the first broadcast
        self.ledger.broadcast_failure_count = 12

        # configure the policy to retry once with a zero delay
        self.policy.broadcast_retries = 10
        self.policy.broadcast_retry_delay = zero_retry_delay

        await self.policy.register()

        self.assertEqual(self.ledger.broadcast_failure_count, 2)
        self.assertIsNone(self.policy.last_successful_registration)

    async def test_retry_on_rpc_poll_failure_succeeds(self):
        # configure the ledger to fail the first broadcast
        self.ledger.rpc_query_failure_count = 4

        # configure the policy to retry once with a zero delay
        self.policy.poll_retries = 5
        self.policy.poll_retry_delay = zero_retry_delay

        await self.policy.register()

        self.assertEqual(self.ledger.rpc_query_failure_count, 0)
        self.assertIsNotNone(self.policy.last_successful_registration)

    async def test_retry_on_rpc_poll_failure_fails(self):
        # configure the ledger to fail the first broadcast
        self.ledger.rpc_query_failure_count = 6

        # configure the policy to retry once with a zero delay
        self.policy.poll_retries = 5
        self.policy.poll_retry_delay = zero_retry_delay

        await self.policy.register()

        self.assertEqual(self.ledger.rpc_query_failure_count, 1)
        self.assertIsNone(self.policy.last_successful_registration)

    async def test_retry_on_poll_failure_succeeds(self):
        # configure the ledger to fail the first broadcast
        self.ledger.query_failure_count = 4

        # configure the policy to retry once with a zero delay
        self.policy.poll_retries = 5
        self.policy.poll_retry_delay = zero_retry_delay

        await self.policy.register()

        self.assertEqual(self.ledger.query_failure_count, 0)
        self.assertIsNotNone(self.policy.last_successful_registration)

    async def test_retry_on_poll_failure_fails(self):
        # configure the ledger to fail the first broadcast
        self.ledger.query_failure_count = 6

        # configure the policy to retry once with a zero delay
        self.policy.poll_retries = 5
        self.policy.poll_retry_delay = zero_retry_delay

        await self.policy.register()

        self.assertEqual(self.ledger.query_failure_count, 1)
        self.assertIsNone(self.policy.last_successful_registration)
