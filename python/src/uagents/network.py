"""Network and Contracts."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List

from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.client import (
    LedgerClient,
    NetworkConfig,
    DEFAULT_QUERY_INTERVAL_SECS,
    DEFAULT_QUERY_TIMEOUT_SECS,
    prepare_and_broadcast_basic_transaction,
)
from cosmpy.aerial.exceptions import NotFoundError, QueryTimeoutError
from cosmpy.aerial.contract.cosmwasm import create_cosmwasm_execute_msg
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.tx_helpers import TxResponse
from cosmpy.aerial.tx import Transaction
from cosmpy.aerial.wallet import LocalWallet

from uagents.config import (
    AgentNetwork,
    CONTRACT_ALMANAC,
    CONTRACT_NAME_SERVICE,
    AGENT_NETWORK,
    AVERAGE_BLOCK_INTERVAL,
    REGISTRATION_FEE,
    REGISTRATION_DENOM,
    get_logger,
)


logger = get_logger("network")

# Setting up the Ledger and Faucet based on Agent Network
if AGENT_NETWORK == AgentNetwork.FETCHAI_TESTNET:
    _ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    _faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
elif AGENT_NETWORK == AgentNetwork.FETCHAI_MAINNET:
    _ledger = LedgerClient(NetworkConfig.fetchai_mainnet())
else:
    raise NotImplementedError


def get_ledger() -> LedgerClient:
    """
    Get the Ledger client.

    Returns:
        LedgerClient: The Ledger client instance.
    """
    return _ledger


def get_faucet() -> FaucetApi:
    """
    Get the Faucet API instance.

    Returns:
        FaucetApi: The Faucet API instance.
    """
    return _faucet_api


async def wait_for_tx_to_complete(
    tx_hash: str,
    timeout: Optional[timedelta] = None,
    poll_period: Optional[timedelta] = None,
) -> TxResponse:
    """
    Wait for a transaction to complete on the Ledger.

    Args:
        tx_hash (str): The hash of the transaction to monitor.
        timeout (Optional[timedelta], optional): The maximum time to wait for
        the transaction to complete. Defaults to None.
        poll_period (Optional[timedelta], optional): The time interval to poll
        the Ledger for the transaction status. Defaults to None.

    Returns:
        TxResponse: The response object containing the transaction details.
    """
    if timeout is None:
        timeout = timedelta(seconds=DEFAULT_QUERY_TIMEOUT_SECS)
    if poll_period is None:
        poll_period = timedelta(seconds=DEFAULT_QUERY_INTERVAL_SECS)
    start = datetime.now()
    while True:
        try:
            return _ledger.query_tx(tx_hash)
        except NotFoundError:
            pass

        delta = datetime.now() - start
        if delta >= timeout:
            raise QueryTimeoutError()

        await asyncio.sleep(poll_period.total_seconds())


class AlmanacContract(LedgerContract):
    """
    A class representing the Almanac contract for agent registration.

    This class provides methods to interact with the Almanac contract, including
    checking if an agent is registered, retrieving the expiry height of an agent's
    registration, and getting the endpoints associated with an agent's registration.

    """

    def is_registered(self, address: str) -> bool:
        """
        Check if an agent is registered in the Almanac contract.

        Args:
            address (str): The agent's address.

        Returns:
            bool: True if the agent is registered, False otherwise.
        """
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            return False
        return True

    def get_expiry(self, address: str) -> int:
        """
        Get the expiry height of an agent's registration.

        Args:
            address (str): The agent's address.

        Returns:
            int: The expiry height of the agent's registration.
        """
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            contract_state = self.query({"query_contract_state": {}})
            expiry = contract_state.get("state").get("expiry_height")
            return expiry * AVERAGE_BLOCK_INTERVAL

        expiry = response.get("record")[0].get("expiry")
        height = response.get("height")

        return (expiry - height) * AVERAGE_BLOCK_INTERVAL

    def get_endpoints(self, address: str):
        """
        Get the endpoints associated with an agent's registration.

        Args:
            address (str): The agent's address.

        Returns:
            Any: The endpoints associated with the agent's registration.
        """
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            return None
        return response.get("record")[0]["record"]["service"]["endpoints"]

    def get_protocols(self, address: str):
        """
        Get the protocols associated with an agent's registration.

        Args:
            address (str): The agent's address.

        Returns:
            Any: The protocols associated with the agent's registration.
        """
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query(query_msg)

        if not response["record"]:
            return None
        return response.get("record")[0]["record"]["service"]["protocols"]

    async def register(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        agent_address: str,
        protocols: List[str],
        endpoints: List[Dict[str, Any]],
        signature: str,
    ):
        """
        Register an agent with the Almanac contract.

        Args:
            ledger (LedgerClient): The Ledger client.
            wallet (LocalWallet): The agent's wallet.
            agent_address (str): The agent's address.
            protocols (List[str]): List of protocols.
            endpoints (List[Dict[str, Any]]): List of endpoint dictionaries.
            signature (str): The agent's signature.
        """
        transaction = Transaction()

        almanac_msg = {
            "register": {
                "record": {
                    "service": {
                        "protocols": protocols,
                        "endpoints": endpoints,
                    }
                },
                "signature": signature,
                "sequence": self.get_sequence(agent_address),
                "agent_address": agent_address,
            }
        }

        transaction.add_message(
            create_cosmwasm_execute_msg(
                wallet.address(),
                self.address,
                almanac_msg,
                funds=f"{REGISTRATION_FEE}{REGISTRATION_DENOM}",
            )
        )

        transaction = prepare_and_broadcast_basic_transaction(
            ledger, transaction, wallet
        )
        await wait_for_tx_to_complete(transaction.tx_hash)

    def get_sequence(self, address: str) -> int:
        """
        Get the agent's sequence number for Almanac registration.

        Args:
            address (str): The agent's address.

        Returns:
            int: The agent's sequence number.
        """
        query_msg = {"query_sequence": {"agent_address": address}}
        sequence = self.query(query_msg)["sequence"]

        return sequence


_almanac_contract = AlmanacContract(None, _ledger, CONTRACT_ALMANAC)


def get_almanac_contract() -> AlmanacContract:
    """
    Get the AlmanacContract instance.

    Returns:
        AlmanacContract: The AlmanacContract instance.
    """
    return _almanac_contract


class NameServiceContract(LedgerContract):
    """
    A class representing the NameService contract for managing domain names and ownership.

    This class provides methods to interact with the NameService contract, including
    checking name availability, checking ownership, querying domain public status,
    obtaining registration transaction details, and registering a name within a domain.

    """

    def is_name_available(self, name: str, domain: str):
        """
        Check if a name is available within a domain.

        Args:
            name (str): The name to check.
            domain (str): The domain to check within.

        Returns:
            bool: True if the name is available, False otherwise.
        """
        query_msg = {"domain_record": {"domain": f"{name}.{domain}"}}
        return self.query(query_msg)["is_available"]

    def is_owner(self, name: str, domain: str, wallet_address: str):
        """
        Check if the provided wallet address is the owner of a name within a domain.

        Args:
            name (str): The name to check ownership for.
            domain (str): The domain to check within.
            wallet_address (str): The wallet address to check ownership against.

        Returns:
            bool: True if the wallet address is the owner, False otherwise.
        """
        query_msg = {
            "permissions": {
                "domain": f"{name}.{domain}",
                "owner": wallet_address,
            }
        }
        permission = self.query(query_msg)["permissions"]
        return permission == "admin"

    def is_domain_public(self, domain: str):
        """
        Check if a domain is public.

        Args:
            domain (str): The domain to check.

        Returns:
            bool: True if the domain is public, False otherwise.
        """
        res = self.query({"domain_record": {"domain": f".{domain}"}})
        return res["is_public"]

    def get_registration_tx(
        self, name: str, wallet_address: str, agent_address: str, domain: str
    ):
        """
        Get the registration transaction for registering a name within a domain.

        Args:
            name (str): The name to be registered.
            wallet_address (str): The wallet address initiating the registration.
            agent_address (str): The address of the agent.
            domain (str): The domain in which the name is registered.

        Returns:
            Optional[Transaction]: The registration transaction, or None if the name is not
            available or not owned by the wallet address.
        """
        if not self.is_name_available(name, domain) and not self.is_owner(
            name, domain, wallet_address
        ):
            return None

        registration_msg = {
            "register": {
                "domain": f"{name}.{domain}",
                "agent_address": agent_address,
            }
        }

        transaction = Transaction()
        transaction.add_message(
            create_cosmwasm_execute_msg(
                wallet_address, CONTRACT_NAME_SERVICE, registration_msg
            )
        )

        return transaction

    async def register(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        agent_address: str,
        name: str,
        domain: str,
    ):
        """
        Register a name within a domain using the NameService contract.

        Args:
            ledger (LedgerClient): The Ledger client.
            wallet (LocalWallet): The wallet of the agent.
            agent_address (str): The address of the agent.
            name (str): The name to be registered.
            domain (str): The domain in which the name is registered.
        """
        logger.info("Registering name...")

        if not get_almanac_contract().is_registered(agent_address):
            logger.warning(
                f"Agent {name} needs to be registered in almanac contract to register its name"
            )
            return

        if not self.is_domain_public(domain):
            logger.warning(
                f"Domain {domain} is not public, please select a public domain"
            )
            return

        transaction = self.get_registration_tx(
            name, str(wallet.address()), agent_address, domain
        )

        if transaction is None:
            logger.error(
                f"Please select another name, {name} is owned by another address"
            )
            return
        transaction = prepare_and_broadcast_basic_transaction(
            ledger, transaction, wallet
        )
        await wait_for_tx_to_complete(transaction.tx_hash)
        logger.info("Registering name...complete")


_name_service_contract = NameServiceContract(None, _ledger, CONTRACT_NAME_SERVICE)


def get_name_service_contract() -> NameServiceContract:
    """
    Get the NameServiceContract instance.

    Returns:
        NameServiceContract: The NameServiceContract instance.
    """
    return _name_service_contract
