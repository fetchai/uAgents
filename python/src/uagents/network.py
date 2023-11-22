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
from cosmpy.aerial.tx import Transaction
from cosmpy.aerial.tx_helpers import TxResponse
from cosmpy.aerial.wallet import LocalWallet

from uagents.config import (
    MAINNET_CONTRACT_ALMANAC,
    TESTNET_CONTRACT_ALMANAC,
    MAINNET_CONTRACT_NAME_SERVICE,
    TESTNET_CONTRACT_NAME_SERVICE,
    AVERAGE_BLOCK_INTERVAL,
    REGISTRATION_FEE,
    REGISTRATION_DENOM,
    get_logger,
)


logger = get_logger("network")


_faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
_testnet_ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
_mainnet_ledger = LedgerClient(NetworkConfig.fetchai_mainnet())


class InsufficientFundsError(Exception):
    """Raised when an agent has insufficient funds for a transaction."""


def get_ledger(test: bool = True) -> LedgerClient:
    """
    Get the Ledger client.

    Args:
        test (bool): Whether to use the testnet or mainnet. Defaults to True.

    Returns:
        LedgerClient: The Ledger client instance.
    """
    if test:
        return _testnet_ledger
    return _mainnet_ledger


def get_faucet() -> FaucetApi:
    """
    Get the Faucet API instance.

    Returns:
        FaucetApi: The Faucet API instance.
    """
    return _faucet_api


def add_testnet_funds(wallet_address: str):
    """
    Add testnet funds to the provided wallet address.

    Args:
        wallet_address (str): The wallet address to add funds to.
    """
    _faucet_api._try_create_faucet_claim(  # pylint: disable=protected-access
        wallet_address
    )


async def wait_for_tx_to_complete(
    tx_hash: str,
    ledger: LedgerClient,
    timeout: Optional[timedelta] = None,
    poll_period: Optional[timedelta] = None,
) -> TxResponse:
    """
    Wait for a transaction to complete on the Ledger.

    Args:
        tx_hash (str): The hash of the transaction to monitor.
        ledger (LedgerClient): The Ledger client to poll.
        timeout (Optional[timedelta], optional): The maximum time to wait.
        the transaction to complete. Defaults to None.
        poll_period (Optional[timedelta], optional): The time interval to poll

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
            return ledger.query_tx(tx_hash)
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
        await wait_for_tx_to_complete(transaction.tx_hash, ledger)

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


_mainnet_almanac_contract = AlmanacContract(
    None, _mainnet_ledger, MAINNET_CONTRACT_ALMANAC
)
_testnet_almanac_contract = AlmanacContract(
    None, _testnet_ledger, TESTNET_CONTRACT_ALMANAC
)


def get_almanac_contract(test: bool = True) -> AlmanacContract:
    """
    Get the AlmanacContract instance.

    Args:
        test (bool): Whether to use the testnet or mainnet. Defaults to True.

    Returns:
        AlmanacContract: The AlmanacContract instance.
    """
    if test:
        return _testnet_almanac_contract
    return _mainnet_almanac_contract


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
        self,
        name: str,
        wallet_address: str,
        agent_address: str,
        domain: str,
        test: bool,
    ):
        """
        Get the registration transaction for registering a name within a domain.

        Args:
            name (str): The name to be registered.
            wallet_address (str): The wallet address initiating the registration.
            agent_address (str): The address of the agent.
            domain (str): The domain in which the name is registered.
            test (bool): The agent type

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

        contract = (
            TESTNET_CONTRACT_NAME_SERVICE if test else MAINNET_CONTRACT_NAME_SERVICE
        )
        transaction = Transaction()
        transaction.add_message(
            create_cosmwasm_execute_msg(wallet_address, contract, registration_msg)
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
        chain_id = ledger.query_chain_id()

        if not get_almanac_contract(chain_id == "dorado-1").is_registered(
            agent_address
        ):
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
            name,
            str(wallet.address()),
            agent_address,
            domain,
            chain_id == "dorado-1",
        )

        if transaction is None:
            logger.error(
                f"Please select another name, {name} is owned by another address"
            )
            return
        transaction = prepare_and_broadcast_basic_transaction(
            ledger, transaction, wallet
        )
        await wait_for_tx_to_complete(transaction.tx_hash, ledger)
        logger.info("Registering name...complete")


_mainnet_name_service_contract = NameServiceContract(
    None, _mainnet_ledger, MAINNET_CONTRACT_NAME_SERVICE
)
_testnet_name_service_contract = NameServiceContract(
    None, _testnet_ledger, TESTNET_CONTRACT_NAME_SERVICE
)


def get_name_service_contract(test: bool = True) -> NameServiceContract:
    """
    Get the NameServiceContract instance.

    Args:
        test (bool): Whether to use the testnet or mainnet. Defaults to True.

    Returns:
        NameServiceContract: The NameServiceContract instance.
    """
    if test:
        return _testnet_name_service_contract
    return _mainnet_name_service_contract
