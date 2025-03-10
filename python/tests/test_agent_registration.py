# pylint: disable=protected-access
import hashlib
import json
import unittest
from typing import Any, Dict, List

# from cosmpy.protos.cosmos.base.v1beta1.coin_pb2 import Coin
from uagents import Agent
from uagents.crypto import Identity, encode_length_prefixed
from uagents.network import get_name_service_contract

# EXPECTED_FUNDS = Coin(amount="8640000000000000", denom="atestfet")


def generate_digest(
    agent_address: str, contract_address: str, sequence: int, wallet_address: str
) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(encode_length_prefixed(contract_address))
    hasher.update(encode_length_prefixed(agent_address))
    hasher.update(encode_length_prefixed(sequence))
    hasher.update(encode_length_prefixed(wallet_address))
    return hasher.digest()


def validate_registration_msg(msg: Dict[str, Any]) -> bool:
    try:
        if "register" not in msg:
            return False

        register = msg["register"]
        if not isinstance(register, dict):
            return False
        if (
            "record" not in register
            or "signature" not in register
            or "sequence" not in register
            or "agent_address" not in register
        ):
            return False

        record = register["record"]
        if not isinstance(record, dict):
            return False
        if "service" not in record:
            return False

        service = record["service"]
        if not isinstance(service, dict):
            return False
        if "protocols" not in service or "endpoints" not in service:
            return False

        if not isinstance(service["protocols"], list) or not all(
            isinstance(protocol, str) for protocol in service["protocols"]
        ):
            return False
        if not isinstance(service["endpoints"], list) or not all(
            isinstance(endpoint, dict) for endpoint in service["endpoints"]
        ):
            return False

        if not isinstance(register["signature"], str):
            return False
        if not isinstance(register["sequence"], int):
            return False
        return isinstance(register["agent_address"], str)
    except KeyError:
        return False


def validate_tx_msgs(
    msgs: List[Any], wallet_address: str, contract_address: str
) -> bool:
    try:
        for msg in msgs:
            if not (msg.sender and msg.contract and msg.msg):
                return False

            if msg.sender != wallet_address or msg.contract != contract_address:
                return False

            try:
                msg_dict = json.loads(msg.msg.decode("utf-8"))
            except (json.JSONDecodeError, AttributeError):
                return False

            if "register" in msg_dict:
                if not msg_dict["register"]["domain"] or not msg.funds[0]:
                    return False
            elif "update_record" in msg_dict:
                update_record = msg_dict["update_record"]
                if not update_record.get("domain") or not update_record.get(
                    "agent_records"
                ):
                    return False
            else:
                return False
        return True
    except KeyError:
        return False


def mock_almanac_registration(almanac_msg: Dict[str, Any], digest: bytes):
    registration = almanac_msg["register"]
    return Identity.verify_digest(
        registration["agent_address"], digest, registration["signature"]
    ) and validate_registration_msg(almanac_msg)


class TestRegistration(unittest.IsolatedAsyncioTestCase):
    async def test_mock_almanac_registration(self):
        agent = Agent(
            endpoint=["http://localhost:8000/submit"], seed="almanact_reg_agent"
        )

        signature = agent.sign_registration(0)

        almanac_msg = agent._almanac_contract.get_registration_msg(
            list(agent.protocols.keys()), agent._endpoints, signature, 0, agent.address
        )

        contract_address = str(agent._almanac_contract.address)

        digest = generate_digest(
            agent.address, contract_address, 0, str(agent.wallet.address())
        )

        self.assertEqual(
            mock_almanac_registration(almanac_msg, digest),
            True,
            "Mock Almanac registration failed",
        )

    async def test_name_service_registration(self):
        agent = Agent(seed="name_reg_agent")

        name_service_contract = get_name_service_contract()

        if not name_service_contract.address:
            self.fail("Name service contract address is invalid")

        tx = name_service_contract.get_registration_tx(
            agent.name, agent.wallet.address(), agent.address, "example.agent", True
        )

        if not tx:
            self.fail("Name service registration TX is invalid")

        self.assertTrue(
            validate_tx_msgs(
                tx.msgs, str(agent.wallet.address()), name_service_contract.address.data
            ),
            "Name service registration TX is invalid",
        )


if __name__ == "__main__":
    unittest.main()
