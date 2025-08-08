"""Network and Contracts."""

import asyncio
import time
from collections.abc import Callable
from logging import Logger
from typing import Any

from cosmpy.aerial.client import (
    DEFAULT_QUERY_INTERVAL_SECS,
    Account,
    LedgerClient,
    NetworkConfig,
    prepare_and_broadcast_basic_transaction,
)
from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.contract.cosmwasm import create_cosmwasm_execute_msg
from cosmpy.aerial.exceptions import NotFoundError, QueryTimeoutError
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.tx import Transaction, TxFee
from cosmpy.aerial.tx_helpers import SubmittedTx, TxResponse
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.address import Address
from uagents_core.identity import Identity
from uagents_core.types import AgentEndpoint, AgentInfo

from uagents.config import (
    ALMANAC_CONTRACT_VERSION,
    ALMANAC_REGISTRATION_WAIT,
    ANAME_REGISTRATION_SECONDS,
    AVERAGE_BLOCK_INTERVAL,
    MAINNET_CONTRACT_ALMANAC,
    MAINNET_CONTRACT_NAME_SERVICE,
    ORACLE_AGENT_DOMAIN,
    TESTNET_CONTRACT_ALMANAC,
    TESTNET_CONTRACT_NAME_SERVICE,
)
from uagents.crypto import sign_registration
from uagents.types import AgentNetwork
from uagents.utils import get_logger

logger: Logger = get_logger("network")


_faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
_testnet_ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
_mainnet_ledger = LedgerClient(NetworkConfig.fetchai_mainnet())

RetryDelayFunc = Callable[[int], float]
DEFAULT_BROADCAST_RETRIES = 5
DEFAULT_POLL_RETRIES = 10
DEFAULT_REGISTRATION_TIMEOUT_BLOCKS = 100


def default_exp_backoff(retry: int) -> float:
    """
    Generate a backoff time starting from 0.64 seconds and limited to ~32 seconds
    """
    return (2 ** (min(retry, 9) + 6)) / 1000


def block_polling_exp_backoff(retry: int) -> float:
    """
    Generate an exponential backoff that is designed for block polling. We keep the
    same default exponential backoff, but it is clamped to the default query interval.
    """
    back_off = default_exp_backoff(retry)
    return max(back_off, DEFAULT_QUERY_INTERVAL_SECS)


class InsufficientFundsError(Exception):
    """Raised when an agent has insufficient funds for a transaction."""


class BroadcastTimeoutError(RuntimeError):
    """Raised when a transaction broadcast fails due to a timeout."""

    def __init__(self):
        super().__init__("Broadcast timeout error")


class AlmanacContractRecord(AgentInfo):
    contract_address: str
    sender_address: str
    timestamp: int | None = None
    signature: str | None = None

    def sign(self, identity: Identity) -> None:
        self.timestamp = int(time.time()) - ALMANAC_REGISTRATION_WAIT
        self.signature = sign_registration(
            identity=identity,
            contract_address=self.contract_address,
            timestamp=self.timestamp,
            wallet_address=self.sender_address,
        )


def get_ledger(network: AgentNetwork = "testnet") -> LedgerClient:
    """
    Get the Ledger client.

    Args:
        network (AgentNetwork, optional): The network to use. Defaults to "testnet".

    Returns:
        LedgerClient: The Ledger client instance.
    """
    return _mainnet_ledger if network == "mainnet" else _testnet_ledger


def get_faucet() -> FaucetApi:
    """
    Get the Faucet API instance.

    Returns:
        FaucetApi: The Faucet API instance.
    """
    return _faucet_api


def add_testnet_funds(wallet_address: str) -> None:
    """
    Add testnet funds to the provided wallet address.

    Args:
        wallet_address (str): The wallet address to add funds to.
    """
    _faucet_api._try_create_faucet_claim(  # pylint: disable=protected-access
        wallet_address
    )


def parse_record_config(
    record: str | list[str] | dict[str, dict] | None,
) -> list[dict[str, Any]] | None:
    """
    Parse the user-provided record configuration.

    Returns:
        list[dict[str, Any]] | None: The parsed record configuration in correct format.
    """
    if isinstance(record, dict):
        records = [
            {"address": val[0], "weight": val[1].get("weight") or 1}
            for val in record.items()
        ]
    elif isinstance(record, list):
        records = [{"address": val, "weight": 1} for val in record]
    elif isinstance(record, str):
        records = [{"address": record, "weight": 1}]
    else:
        records = None
    return records


async def wait_for_tx_to_complete(
    tx_hash: str,
    ledger: LedgerClient,
    *,
    poll_retries: int | None = None,
    poll_retry_delay: RetryDelayFunc | None = None,
) -> TxResponse:
    """
    Wait for a transaction to complete on the Ledger.

    Args:
        tx_hash (str): The hash of the transaction to monitor.
        ledger (LedgerClient): The Ledger client to poll.
        poll_retries (int, optional): The maximum number of retry attempts.
        poll_retry_delay (RetryDelayFunc, optional): The retry delay function,
            if not provided the default exponential backoff will be used.

    Returns:
        TxResponse: The response object containing the transaction details.
    """
    delay_func = poll_retry_delay or block_polling_exp_backoff
    response: TxResponse | None = None
    for n in range(poll_retries or DEFAULT_POLL_RETRIES):
        try:
            response = ledger.query_tx(tx_hash)
            break
        except NotFoundError:
            pass
        except Exception:
            pass

        await asyncio.sleep(delay_func(n))

    if response is None:
        raise QueryTimeoutError()

    return response


class AlmanacContract(LedgerContract):
    """
    A class representing the Almanac contract for agent registration.

    This class provides methods to interact with the Almanac contract, including
    checking if an agent is registered, retrieving the expiry height of an agent's
    registration, and getting the endpoints associated with an agent's registration.
    """

    def check_version(self) -> bool:
        """
        Check if the contract version supported by this version of uAgents matches the
        deployed version.

        Returns:
            bool: True if the contract version is supported, False otherwise.
        """
        try:
            deployed_version = self.get_contract_version()

            # parse major and minor versions
            deployed_major_version = deployed_version.split(".")[0]
            supported_major_version = ALMANAC_CONTRACT_VERSION.split(".")[0]

            if supported_major_version != deployed_major_version:
                logger.warning(
                    f"The deployed version of the Almanac Contract is {deployed_version} "
                    f"and you are using version {ALMANAC_CONTRACT_VERSION}. "
                    "Update uAgents to the latest version to enable contract interactions.",
                )
                return False
        except Exception as e:
            logger.error(
                "Failed to query contract version. Contract interactions will be disabled."
            )
            logger.debug(e)
            return False
        return True

    def query_contract(self, query_msg: dict[str, Any]) -> Any:
        """
        Execute a query with additional checks and error handling.

        Args:
            query_msg (dict[str, Any]): The query message.

        Returns:
            Any: The query response.

        Raises:
            RuntimeError: If the contract address is not set or the query fails.
        """
        try:
            response = self.query(query_msg)
            if not isinstance(response, dict):
                raise ValueError("Invalid response format")
            return response
        except Exception as e:
            logger.error(f"Query failed with error: {e.__class__.__name__}.")
            logger.debug(e)
            raise

    def get_contract_version(self) -> str:
        """
        Get the version of the contract.

        Returns:
            str: The version of the contract.
        """
        query_msg = {"query_contract_state": {}}
        response = self.query_contract(query_msg)

        return response["contract_version"]

    def get_registration_fee(self, wallet_address: Address | None = None) -> int:
        """
        Get the registration fee for the contract.

        Returns:
            int: The registration fee.
        """

        if wallet_address:
            role_query_msg = {
                "access_control": {
                    "query_has_role": {
                        "role": "clearing_registrar",
                        "addr": str(wallet_address),
                    }
                }
            }
            role_response = self.query_contract(role_query_msg)
            if role_response.get("has_role"):
                return 0

        query_msg = {"query_contract_state": {}}
        response = self.query_contract(query_msg)

        return int(response["state"]["register_stake_amount"])

    def is_registered(self, address: str) -> bool:
        """
        Check if an agent is registered in the Almanac contract.

        Args:
            address (str): The agent's address.

        Returns:
            bool: True if the agent is registered, False otherwise.
        """
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query_contract(query_msg)

        return bool(response.get("record"))

    def registration_needs_update(
        self,
        address: str,
        endpoints: list[AgentEndpoint],
        protocols: list[str],
        min_seconds_left: int,
    ) -> bool:
        """
        Check if an agent's registration needs to be updated.

        Args:
            address (str): The agent's address.
            endpoints (list[AgentEndpoint]): The agent's endpoints.
            protocols (list[str]): The agent's protocols.
            min_time_left (int): The minimum time left before the agent's registration expires

        Returns:
            bool: True if the agent's registration needs to be updated or will expire sooner
                than the specified minimum time, False otherwise.
        """
        seconds_to_expiry, registered_endpoints, registered_protocols = (
            self.query_agent_record(address)
        )
        return (
            not self.is_registered(address)
            or seconds_to_expiry < min_seconds_left
            or endpoints != registered_endpoints
            or protocols != registered_protocols
        )

    def query_agent_record(
        self, address: str
    ) -> tuple[int, list[AgentEndpoint], list[str]]:
        """
        Get the records associated with an agent's registration.

        Args:
            address (str): The agent's address.

        Returns:
            tuple[int, list[AgentEndpoint], list[str]]: The expiry height of the agent's
            registration, the agent's endpoints, and the agent's protocols.
        """
        query_msg = {"query_records": {"agent_address": address}}
        response = self.query_contract(query_msg)

        if not response.get("record"):
            return 0, [], []

        if not response.get("record"):
            contract_state = self.query_contract({"query_contract_state": {}})
            expiry = contract_state.get("state", {}).get("expiry_height", 0)
            return expiry * AVERAGE_BLOCK_INTERVAL

        expiry_block = response["record"][0].get("expiry", 0)
        current_block = response.get("height", 0)

        seconds_to_expiry = (expiry_block - current_block) * AVERAGE_BLOCK_INTERVAL

        endpoints = []
        for endpoint in response["record"][0]["record"]["service"]["endpoints"]:
            endpoints.append(AgentEndpoint.model_validate(endpoint))

        protocols = response["record"][0]["record"]["service"]["protocols"]

        return seconds_to_expiry, endpoints, protocols

    def get_expiry(self, address: str) -> int:
        """
        Get the approximate seconds to expiry of an agent's registration.

        Args:
            address (str): The agent's address.

        Returns:
            int: The approximate seconds to expiry of the agent's registration.
        """
        return self.query_agent_record(address)[0]

    def get_endpoints(self, address: str) -> list[AgentEndpoint]:
        """
        Get the endpoints associated with an agent's registration.

        Args:
            address (str): The agent's address.

        Returns:
            list[AgentEndpoint]: The agent's registered endpoints.
        """
        return self.query_agent_record(address)[1]

    def get_protocols(self, address: str) -> list[str]:
        """
        Get the protocols associated with an agent's registration.

        Args:
            address (str): The agent's address.

        Returns:
            list[str]: The agent's registered protocols.
        """
        return self.query_agent_record(address)[2]

    def get_registration_msg(
        self,
        protocols: list[str],
        endpoints: list[AgentEndpoint],
        signature: str,
        sequence: int,
        address: str,
    ) -> dict[str, Any]:
        return {
            "register": {
                "record": {
                    "service": {
                        "protocols": protocols,
                        "endpoints": [e.model_dump() for e in endpoints],
                    }
                },
                "signature": signature,
                "sequence": sequence,
                "agent_address": address,
            }
        }

    async def register(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        agent_address: str,
        protocols: list[str],
        endpoints: list[AgentEndpoint],
        signature: str,
        current_time: int,
        *,
        broadcast_retries: int | None = None,
        broadcast_retry_delay: RetryDelayFunc | None = None,
        poll_retries: int | None = None,
        poll_retry_delay: RetryDelayFunc | None = None,
        tx_fee: TxFee | None = None,
        timeout_blocks: int = DEFAULT_REGISTRATION_TIMEOUT_BLOCKS,
    ) -> TxResponse:
        """
        Register an agent with the Almanac contract.

        Args:
            ledger (LedgerClient): The Ledger client.
            wallet (LocalWallet): The agent's wallet.
            agent_address (str): The agent's address.
            protocols (list[str]): List of protocols.
            endpoints (list[dict[str, Any]]): List of endpoint dictionaries.
            signature (str): The agent's signature.
            current_time (int): The current time in seconds since the epoch.
            broadcast_retries (int, optional): The number of retries for broadcasting.
            broadcast_retry_delay (RetryDelayFunc, optional): The delay function for retries.
            poll_retries (int, optional): The number of retries for polling.
            poll_retry_delay (RetryDelayFunc, optional): The delay function for polling.
            tx_fee (TxFee, optional): The transaction fee to use.
            timeout_blocks (int, optional): The number of blocks to wait before timing out.

        Returns:
            TxResponse: The transaction response.
        """
        if not self.address:
            raise ValueError("Contract address not set")

        transaction = Transaction()

        almanac_msg = self.get_registration_msg(
            protocols=protocols,
            endpoints=endpoints,
            signature=signature,
            sequence=current_time,
            address=agent_address,
        )

        denom = self._client.network_config.fee_denomination
        fee = self.get_registration_fee(wallet.address())
        funds = f"{fee}{denom}" if fee else None
        transaction.add_message(
            create_cosmwasm_execute_msg(
                sender_address=wallet.address(),
                contract_address=self.address,
                args=almanac_msg,
                funds=funds,
            )
        )

        # cache the account details
        account: Account = ledger.query_account(wallet.address())

        # attempt to broadcast the transaction to the network
        broadcast_delay_func = broadcast_retry_delay or default_exp_backoff
        num_broadcast_retries = broadcast_retries or DEFAULT_BROADCAST_RETRIES

        tx: SubmittedTx | None = None
        for n in range(num_broadcast_retries):
            timeout_height = ledger.query_height() + timeout_blocks
            try:
                tx = prepare_and_broadcast_basic_transaction(
                    ledger,
                    transaction,
                    wallet,
                    account=account,
                    fee=tx_fee,
                    timeout_height=timeout_height,
                )
                break
            except RuntimeError:
                await asyncio.sleep(broadcast_delay_func(n))

        if tx is None:
            raise BroadcastTimeoutError()

        status: TxResponse = await wait_for_tx_to_complete(
            tx_hash=tx.tx_hash,
            ledger=ledger,
            poll_retries=poll_retries,
            poll_retry_delay=poll_retry_delay,
        )
        if status.code != 0:
            raise RuntimeError(
                f"Registration transaction failed ({status.code}): {status.hash})"
            )

        return status

    async def register_batch(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        agent_records: list[AlmanacContractRecord],
        *,
        broadcast_retries: int | None = None,
        broadcast_retry_delay: RetryDelayFunc | None = None,
        poll_retries: int | None = None,
        poll_retry_delay: RetryDelayFunc | None = None,
        tx_fee: TxFee | None = None,
        timeout_blocks: int = DEFAULT_REGISTRATION_TIMEOUT_BLOCKS,
    ) -> TxResponse:
        """
        Register multiple agents with the Almanac contract.

        Args:
            ledger (LedgerClient): The Ledger client.
            wallet (LocalWallet): The wallet of the registration sender.
            agent_records (list[ALmanacContractRecord]): The list of agent records to register.
            broadcast_retries (int, optional): The number of retries for broadcasting.
            broadcast_retry_delay (RetryDelayFunc, optional): The delay function for retries.
            poll_retries (int, optional): The number of retries for polling.
            poll_retry_delay (RetryDelayFunc, optional): The delay function for polling.
            tx_fee (TxFee, optional): The transaction fee to use.
            timeout_blocks (int, optional): The number of blocks to wait before timing out.

        Returns:
            TxResponse: The transaction response.
        """
        if not self.address:
            raise ValueError("Contract address not set")

        transaction = Transaction()

        for record in agent_records:
            if record.timestamp is None:
                raise ValueError("Agent record is missing timestamp")

            if record.signature is None:
                raise ValueError("Agent record is not signed")

            almanac_msg = self.get_registration_msg(
                protocols=record.protocols,
                endpoints=record.endpoints,
                signature=record.signature,
                sequence=record.timestamp,
                address=record.address,
            )

            denom = self._client.network_config.fee_denomination
            fee = self.get_registration_fee(wallet.address())
            funds = f"{fee}{denom}" if fee else None
            transaction.add_message(
                create_cosmwasm_execute_msg(
                    sender_address=wallet.address(),
                    contract_address=self.address,
                    args=almanac_msg,
                    funds=funds,
                )
            )

        # cache the account details
        account: Account = ledger.query_account(wallet.address())

        # attempt to broadcast the transaction to the network
        broadcast_delay_func = broadcast_retry_delay or default_exp_backoff
        num_broadcast_retries = broadcast_retries or DEFAULT_BROADCAST_RETRIES
        timeout_height = ledger.query_height() + timeout_blocks

        tx: SubmittedTx | None = None
        for n in range(num_broadcast_retries):
            try:
                tx = prepare_and_broadcast_basic_transaction(
                    ledger,
                    transaction,
                    wallet,
                    account=account,
                    fee=tx_fee,
                    timeout_height=timeout_height,
                )
                break
            except RuntimeError:
                await asyncio.sleep(broadcast_delay_func(n))

        if tx is None:
            raise BroadcastTimeoutError()

        status: TxResponse = await wait_for_tx_to_complete(
            tx_hash=tx.tx_hash,
            ledger=ledger,
            poll_retries=poll_retries,
            poll_retry_delay=poll_retry_delay,
        )
        if status.code != 0:
            raise RuntimeError(
                f"Registration transaction failed ({status.code}): {status.hash})"
            )

        return status

    def get_sequence(self, address: str) -> int:
        """
        Get the agent's sequence number for Almanac registration.

        Args:
            address (str): The agent's address.

        Returns:
            int: The agent's sequence number.
        """
        query_msg = {"query_sequence": {"agent_address": address}}
        sequence = self.query_contract(query_msg)["sequence"]

        return sequence


_mainnet_almanac_contract = AlmanacContract(
    None, _mainnet_ledger, Address(MAINNET_CONTRACT_ALMANAC)
)
_testnet_almanac_contract = AlmanacContract(
    None, _testnet_ledger, Address(TESTNET_CONTRACT_ALMANAC)
)


def get_almanac_contract(network: AgentNetwork = "testnet") -> AlmanacContract | None:
    """
    Get the AlmanacContract instance.

    Args:
        network (AgentNetwork): The network to use. Defaults to "testnet".

    Returns:
        AlmanacContract | None: The AlmanacContract instance if version is supported.
    """
    if network == "mainnet" and _mainnet_almanac_contract.check_version():
        return _mainnet_almanac_contract
    if _testnet_almanac_contract.check_version():
        return _testnet_almanac_contract
    return None


class NameServiceContract(LedgerContract):
    """
    A class representing the NameService contract for managing domain names and ownership.

    This class provides methods to interact with the NameService contract, including
    checking name availability, checking ownership, querying domain public status,
    obtaining registration transaction details, and registering a name within a domain.
    """

    def query_contract(self, query_msg: dict[str, Any]) -> Any:
        """
        Execute a query with additional checks and error handling.

        Args:
            query_msg (dict[str, Any]): The query message.

        Returns:
            Any: The query response.

        Raises:
            ValueError: If the response from contract is not a dict.
        """
        try:
            response = self.query(query_msg)
            if not isinstance(response, dict):
                raise ValueError("Invalid response format")
            return response
        except Exception as e:
            logger.error(f"Querying NameServiceContract failed for query {query_msg}.")
            logger.debug(e)
            raise

    def get_oracle_agent_address(self):
        query_msg = {"query_domain_record": {"domain": ORACLE_AGENT_DOMAIN}}
        return self.query_contract(query_msg)["record"]["records"][0]["agent_address"][
            "records"
        ][0]["address"]

    def is_name_available(self, name: str, domain: str) -> bool:
        """
        Check if a name is available within a domain.

        Args:
            name (str): The name to check.
            domain (str): The domain to check within.

        Returns:
            bool: True if the name is available, False otherwise.
        """
        query_msg = {"query_domain_record": {"domain": f"{name}.{domain}"}}
        return self.query_contract(query_msg)["is_available"]

    def is_owner(self, name: str, domain: str, wallet_address: str) -> bool:
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
            "query_domain_permissions": {
                "domain": f"{name}.{domain}",
                "owner": wallet_address,
            }
        }
        permission = self.query_contract(query_msg)["permissions"]
        return permission == "admin"

    def is_domain_public(self, domain: str) -> bool:
        """
        Check if a domain is public.

        Args:
            domain (str): The domain to check.

        Returns:
            bool: True if the domain is public, False otherwise.
        """
        res = self.query_contract(
            {"query_domain_flags": {"domain": domain.split(".")[-1]}}
        ).get("domain_flags")
        if res:
            return res["web3_flags"]["is_public"]
        return False

    def get_previous_records(self, name: str, domain: str):
        """
        Retrieve the previous records for a given name within a specified domain.

        Args:
            name (str): The name whose records are to be retrieved.
            domain (str): The domain within which the name is registered.

        Returns:
            A list of dictionaries, where each dictionary contains
            details of a record associated with the given name.
        """
        query_msg = {"query_domain_record": {"domain": f"{name}.{domain}"}}
        result = self.query_contract(query_msg)
        if result["record"] is not None:
            return result["record"]["records"][0]["agent_address"]["records"]
        return []

    def get_registration_tx(
        self,
        name: str,
        wallet_address: Address,
        agent_records: list[dict[str, Any]] | str,
        domain: str,
        duration: int,
        network: AgentNetwork,
        approval_token: str,
    ) -> Transaction | None:
        """
        Get the registration transaction for registering a name within a domain.

        Args:
            name (str): The name to be registered.
            wallet_address (str): The wallet address initiating the registration.
            agent_address (str): The address of the agent.
            domain (str): The domain in which the name is registered.
            duration (int): The duration in seconds for which the name is to be registered.
            network (AgentNetwork): The network in which the transaction is executed.
            approval_token (str): The approval token required for registration.

        Returns:
            Transaction | None: The registration transaction, or None if the name is not
            available or not owned by the wallet address.
        """
        transaction = Transaction()

        contract = Address(
            MAINNET_CONTRACT_NAME_SERVICE
            if network == "mainnet"
            else TESTNET_CONTRACT_NAME_SERVICE
        )

        if self.is_name_available(name, domain):
            price_per_second = self.query_contract({"query_contract_state": {}})[
                "price_per_second"
            ]
            amount = int(price_per_second["amount"]) * duration
            denom = price_per_second["denom"]

            registration_msg = {
                "register_domain": {
                    "domain": f"{name}.{domain}",
                    "approval_token": approval_token,
                }
            }

            transaction.add_message(
                create_cosmwasm_execute_msg(
                    sender_address=wallet_address,
                    contract_address=contract,
                    args=registration_msg,
                    funds=f"{amount}{denom}",
                )
            )
        elif not self.is_owner(name, domain, str(wallet_address)):
            return None

        record_msg = {
            "update_domain_record": {
                "domain": f"{name}.{domain}",
                "agent_records": agent_records,
            }
        }

        transaction.add_message(
            create_cosmwasm_execute_msg(
                sender_address=wallet_address,
                contract_address=contract,
                args=record_msg,
            )
        )

        return transaction

    async def register(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        agent_records: str | list[str] | dict[str, dict] | None,
        name: str,
        domain: str,
        approval_token: str,
        duration: int = ANAME_REGISTRATION_SECONDS,
        overwrite: bool = True,
        tx_fee: TxFee | None = None,
        timeout_blocks: int = DEFAULT_REGISTRATION_TIMEOUT_BLOCKS,
    ) -> TxResponse:
        """
        Register a name within a domain using the NameService contract.

        Args:
            ledger (LedgerClient): The Ledger client.
            wallet (LocalWallet): The wallet of the agent.
            agent_records (str | list[str] | dict[str, dict] | None): The agent records
                to be registered.
            name (str): The name to be registered.
            domain (str): The domain in which the name is registered.
            duration (int): The duration in seconds for which the name is to be registered.
            approval_token (str): The approval token required for registration.
            overwrite (bool, optional): Specifies whether to overwrite any existing
                addresses registered to the domain. If False, the address will be
                appended to the previous records. Defaults to True.
            tx_fee (TxFee, optional): The transaction fee to use.
            timeout_blocks (int, optional): The number of blocks to wait before timing out.

        Returns:
            TxResponse: The transaction response.
        """
        logger.info("Registering name...")
        chain_id = ledger.query_chain_id()
        network = (
            "mainnet"
            if chain_id == NetworkConfig.fetchai_mainnet().chain_id
            else "testnet"
        )

        records = parse_record_config(agent_records)
        if not records:
            raise ValueError("Invalid record configuration")
        agent_addresses = [val.get("address") for val in records]

        for agent_address in agent_addresses:
            if not isinstance(agent_address, str):
                logger.warning("Invalid agent address")
                continue
            contract = get_almanac_contract(network)
            if not contract or not contract.is_registered(agent_address):
                raise RuntimeError(
                    "Address %s needs to be registered in almanac contract "
                    "to be registered in a domain.",
                    agent_address,
                )

        if not self.is_domain_public(domain):
            raise RuntimeError(
                f"Domain {domain} is not public, please select a public domain"
            )

        if not overwrite:
            previous_records = self.get_previous_records(name, domain)
            records = list(
                {
                    f"{rec['address']}_{rec['weight']}": rec
                    for rec in previous_records + records
                }.values()
            )

        transaction: Transaction | None = self.get_registration_tx(
            name=name,
            wallet_address=wallet.address(),
            agent_records=records,
            domain=domain,
            duration=duration,
            network=network,
            approval_token=approval_token,
        )

        if transaction is None:
            raise RuntimeError(
                f"Domain {name}.{domain} is not available or not owned by the wallet address."
            )
        timeout_height = ledger.query_height() + timeout_blocks
        submitted_transaction: SubmittedTx = prepare_and_broadcast_basic_transaction(
            client=ledger,
            tx=transaction,
            sender=wallet,
            fee=tx_fee,
            timeout_height=timeout_height,
        )
        status: TxResponse = await wait_for_tx_to_complete(
            submitted_transaction.tx_hash, ledger
        )
        if status.code != 0:
            raise RuntimeError(f"Transaction failed ({status.code}): {status.hash})")
        logger.info("Registering name...complete")
        return status

    async def unregister(
        self,
        name: str,
        domain: str,
        wallet: LocalWallet,
    ) -> None:
        """
        Unregister a name within a domain using the NameService contract.

        Args:
            name (str): The name to be unregistered.
            domain (str): The domain in which the name is registered.
            wallet (LocalWallet): The wallet of the agent.
        """
        logger.info("Unregistering name...")

        if self.is_name_available(name, domain):
            logger.warning("Nothing to unregister... (name is not registered)")
            return

        msg = {
            "remove_domain": {
                "domain": f"{name}.{domain}",
            }
        }
        self.execute(msg, wallet).wait_to_complete()

        logger.info("Unregistering name...complete")


_mainnet_name_service_contract = NameServiceContract(
    None, _mainnet_ledger, Address(MAINNET_CONTRACT_NAME_SERVICE)
)
_testnet_name_service_contract = NameServiceContract(
    None, _testnet_ledger, Address(TESTNET_CONTRACT_NAME_SERVICE)
)


def get_name_service_contract(network: AgentNetwork = "testnet") -> NameServiceContract:
    """
    Get the NameServiceContract instance.

    Args:
        network (AgentNetwork, optional): The network to use. Defaults to "testnet".

    Returns:
        NameServiceContract: The NameServiceContract instance.
    """
    if network == "mainnet":
        return _mainnet_name_service_contract
    return _testnet_name_service_contract
