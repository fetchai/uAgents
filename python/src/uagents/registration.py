import asyncio
import contextlib
import json
import logging
import time
from datetime import datetime
from typing import Any

import aiohttp
import grpc
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.tx import TxFee
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.address import Address
from pydantic import BaseModel
from uagents_core.identity import Identity, parse_identifier
from uagents_core.registration import (
    AgentRegistrationAttestation,
    AgentRegistrationPolicy,
    BatchRegistrationPolicy,
    VerifiableModel,
)
from uagents_core.types import AgentEndpoint, AgentInfo

from uagents.config import (
    ALMANAC_API_MAX_RETRIES,
    ALMANAC_API_TIMEOUT_SECONDS,
    ALMANAC_API_URL,
    ALMANAC_REGISTRATION_WAIT,
    REGISTRATION_UPDATE_INTERVAL_SECONDS,
)
from uagents.crypto import sign_registration
from uagents.network import (
    DEFAULT_REGISTRATION_TIMEOUT_BLOCKS,
    AlmanacContract,
    AlmanacContractRecord,
    InsufficientFundsError,
    RetryDelayFunc,
    add_testnet_funds,
    default_exp_backoff,
)


class AgentRegistrationAttestationBatch(BaseModel):
    attestations: list[AgentRegistrationAttestation]


class AgentStatusUpdate(VerifiableModel):
    is_active: bool


def coerce_metadata_to_str(
    metadata: dict[str, Any] | None,
) -> dict[str, str | dict[str, str]] | None:
    """Step through the metadata and convert any non-string values to strings."""
    if metadata is None:
        return None
    out = {}
    for key, val in metadata.items():
        if isinstance(val, dict):
            out[key] = {
                k: v if isinstance(v, str) else json.dumps(v) for k, v in val.items()
            }
        else:
            out[key] = val if isinstance(val, str) else json.dumps(val)
    return out


def extract_geo_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Extract geo-location metadata from the metadata dictionary."""
    if metadata is None:
        return None
    return {k: v for k, v in metadata.items() if k == "geolocation"}


async def almanac_api_post(
    url: str,
    data: BaseModel,
    *,
    timeout: float | None = None,
    max_retries: int | None = None,
    retry_delay: RetryDelayFunc | None = None,
) -> bool:
    """Send a POST request to the Almanac API."""
    timeout_seconds = timeout or ALMANAC_API_TIMEOUT_SECONDS
    num_retries = max_retries or ALMANAC_API_MAX_RETRIES
    retry_delay_func = retry_delay or default_exp_backoff

    async with aiohttp.ClientSession() as session:
        for retry in range(num_retries):
            try:
                async with session.post(
                    url=url,
                    headers={"content-type": "application/json"},
                    data=data.model_dump_json(),
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds),
                ) as resp:
                    resp.raise_for_status()
                    return True
            except (aiohttp.ClientError, asyncio.exceptions.TimeoutError) as e:
                if retry + 1 >= num_retries:
                    raise e

                await asyncio.sleep(retry_delay_func(retry))
    return False


class AlmanacApiRegistrationPolicy(AgentRegistrationPolicy):
    def __init__(
        self,
        *,
        almanac_api: str | None = None,
        timeout: float | None = None,
        max_retries: int = ALMANAC_API_MAX_RETRIES,
        retry_delay: RetryDelayFunc | None = None,
        logger: logging.Logger | None = None,
    ):
        self._almanac_api = almanac_api or ALMANAC_API_URL
        self._timeout = timeout or ALMANAC_API_TIMEOUT_SECONDS
        self._max_retries = max_retries
        self._logger = logger or logging.getLogger(__name__)
        self._retry_delay = retry_delay or default_exp_backoff
        self._last_successful_registration: datetime | None = None

    @property
    def last_successful_registration(self) -> datetime | None:
        return self._last_successful_registration

    async def register(
        self,
        agent_identifier: str,
        identity: Identity,
        protocols: list[str],
        endpoints: list[AgentEndpoint],
        metadata: dict[str, Any] | None = None,
    ):
        # create the attestation
        attestation = AgentRegistrationAttestation(
            agent_identifier=agent_identifier,
            protocols=protocols,
            endpoints=endpoints,
            metadata=coerce_metadata_to_str(extract_geo_metadata(metadata)),
        )

        # sign the attestation
        attestation.sign(identity)

        try:
            success = await almanac_api_post(
                url=f"{self._almanac_api}/agents",
                data=attestation,
                timeout=self._timeout,
                max_retries=self._max_retries,
                retry_delay=self._retry_delay,
            )
            if success:
                self._logger.info("Registration on Almanac API successful")
                self._last_successful_registration = datetime.now()
            else:
                self._logger.warning("Registration on Almanac API failed")
        except Exception:
            self._logger.warning("Registration on Almanac API failed")


class BatchAlmanacApiRegistrationPolicy(BatchRegistrationPolicy):
    def __init__(
        self,
        almanac_api: str | None = None,
        logger: logging.Logger | None = None,
        timeout: float | None = None,
        max_retries: int = ALMANAC_API_MAX_RETRIES,
        retry_delay: RetryDelayFunc | None = None,
    ):
        self._almanac_api = almanac_api or ALMANAC_API_URL
        self._attestations: list[AgentRegistrationAttestation] = []
        self._logger = logger or logging.getLogger(__name__)
        self._timeout = timeout or ALMANAC_API_TIMEOUT_SECONDS
        self._max_retries = max_retries
        self._retry_delay = retry_delay or default_exp_backoff
        self._last_successful_registration: datetime | None = None

    @property
    def last_successful_registration(self) -> datetime | None:
        return self._last_successful_registration

    def add_agent(self, agent_info: AgentInfo, identity: Identity):
        attestation = AgentRegistrationAttestation(
            agent_identifier=f"{agent_info.prefix}://{agent_info.address}",
            protocols=list(agent_info.protocols),
            endpoints=agent_info.endpoints,
            metadata=coerce_metadata_to_str(extract_geo_metadata(agent_info.metadata)),
        )
        attestation.sign(identity)
        self._attestations.append(attestation)

    async def register(self):
        if not self._attestations:
            return
        attestations = AgentRegistrationAttestationBatch(
            attestations=self._attestations
        )

        try:
            success = await almanac_api_post(
                url=f"{self._almanac_api}/agents/batch",
                data=attestations,
                timeout=self._timeout,
                max_retries=self._max_retries,
                retry_delay=self._retry_delay,
            )
            if success:
                self._logger.info("Batch registration on Almanac API successful")
                self._last_successful_registration = datetime.now()
            else:
                self._logger.warning("Batch registration on Almanac API failed")
        except Exception:
            self._logger.warning("Batch registration on Almanac API failed")


class LedgerBasedRegistrationPolicy(AgentRegistrationPolicy):
    def __init__(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        almanac_contract: AlmanacContract,
        testnet: bool,
        *,
        tx_fee: TxFee | None = None,
        timeout_blocks: int = DEFAULT_REGISTRATION_TIMEOUT_BLOCKS,
        logger: logging.Logger | None = None,
    ):
        self._wallet = wallet
        self._ledger = ledger
        self._testnet = testnet
        self._almanac_contract = almanac_contract
        self._registration_fee = almanac_contract.get_registration_fee(wallet.address())
        self._logger = logger or logging.getLogger(__name__)
        self._broadcast_retries: int | None = None
        self._broadcast_retry_delay: RetryDelayFunc | None = None
        self._poll_retries: int | None = None
        self._poll_retry_delay: RetryDelayFunc | None = None
        self._last_successful_registration: datetime | None = None
        self._timeout_blocks = timeout_blocks
        self._tx_fee = tx_fee

    @property
    def last_successful_registration(self) -> datetime | None:
        return self._last_successful_registration

    @property
    def broadcast_retries(self) -> int | None:
        return self._broadcast_retries

    @broadcast_retries.setter
    def broadcast_retries(self, value: int | None) -> None:
        self._broadcast_retries = value

    @property
    def broadcast_retry_delay(self) -> RetryDelayFunc | None:
        return self._broadcast_retry_delay

    @broadcast_retry_delay.setter
    def broadcast_retry_delay(self, value: RetryDelayFunc | None) -> None:
        self._broadcast_retry_delay = value

    @property
    def poll_retries(self) -> int | None:
        return self._poll_retries

    @poll_retries.setter
    def poll_retries(self, value: int | None) -> None:
        self._poll_retries = value

    @property
    def poll_retry_delay(self) -> RetryDelayFunc | None:
        return self._poll_retry_delay

    @poll_retry_delay.setter
    def poll_retry_delay(self, value: RetryDelayFunc | None) -> None:
        self._poll_retry_delay = value

    async def register(
        self,
        agent_identifier: str,
        identity: Identity,
        protocols: list[str],
        endpoints: list[AgentEndpoint],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Register the agent on the Almanac contract if registration is about to expire or
        the registration data has changed.
        """
        _, _, agent_address = parse_identifier(agent_identifier)

        if (
            not self._almanac_contract.is_registered(agent_address)
            or self._almanac_contract.get_expiry(agent_address)
            < REGISTRATION_UPDATE_INTERVAL_SECONDS
            or endpoints != self._almanac_contract.get_endpoints(agent_address)
            or protocols != self._almanac_contract.get_protocols(agent_address)
        ):
            if self._get_balance() < self._registration_fee:
                self._logger.warning(
                    "I do not have enough funds to register on Almanac contract"
                )
                if self._testnet:
                    add_testnet_funds(str(self._wallet.address()))
                    self._logger.info(
                        f"Adding testnet funds to {self._wallet.address()}"
                    )
                else:
                    self._logger.info(
                        f"Send funds to wallet address: {self._wallet.address()}"
                    )
                raise InsufficientFundsError()

            self._logger.info("Registering on almanac contract...")

            current_time = int(time.time()) - ALMANAC_REGISTRATION_WAIT

            signature = self._sign_registration(identity, current_time)
            try:
                await self._almanac_contract.register(
                    ledger=self._ledger,
                    wallet=self._wallet,
                    agent_address=agent_address,
                    protocols=protocols,
                    endpoints=endpoints,
                    signature=signature,
                    current_time=current_time,
                    broadcast_retries=self._broadcast_retries,
                    broadcast_retry_delay=self._broadcast_retry_delay,
                    poll_retries=self._poll_retries,
                    poll_retry_delay=self._poll_retry_delay,
                    tx_fee=self._tx_fee,
                    timeout_blocks=self._timeout_blocks,
                )
                self._logger.info("Registering on almanac contract...complete")
                self._last_successful_registration = datetime.now()

            except RuntimeError as e:
                self._logger.warning(
                    "Registering on almanac contract...failed (will retry later)"
                )
                self._logger.debug(e)
            except grpc.RpcError as e:
                self._logger.warning(
                    "Registering on almanac contract...failed (will retry later)"
                )
                self._logger.debug(e)

        else:
            self._logger.info("Almanac contract registration is up to date!")

    def _get_balance(self) -> int:
        return self._ledger.query_bank_balance(Address(self._wallet.address()))

    def _sign_registration(self, identity: Identity, timestamp: int) -> str:
        """
        Sign the registration data for Almanac contract.

        Args:
            timestamp (int): The timestamp for the registration.

        Returns:
            str: The signature of the registration data.

        Raises:
            AssertionError: If the Almanac contract address is None.
        """
        assert self._almanac_contract.address is not None

        return sign_registration(
            identity=identity,
            contract_address=str(self._almanac_contract.address),
            timestamp=timestamp,
            wallet_address=str(self._wallet.address()),
        )


class BatchLedgerRegistrationPolicy(BatchRegistrationPolicy):
    def __init__(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        almanac_contract: AlmanacContract,
        testnet: bool,
        *,
        logger: logging.Logger | None = None,
        tx_fee: TxFee | None = None,
        timeout_blocks: int = DEFAULT_REGISTRATION_TIMEOUT_BLOCKS,
    ):
        self._ledger = ledger
        self._wallet = wallet
        self._almanac_contract = almanac_contract
        self._testnet = testnet
        self._registration_fee = almanac_contract.get_registration_fee(wallet.address())
        self._logger = logger or logging.getLogger(__name__)
        self._records: list[AlmanacContractRecord] = []
        self._identities: dict[str, Identity] = {}

        self._broadcast_retries: int | None = None
        self._broadcast_retry_delay: RetryDelayFunc | None = None
        self._poll_retries: int | None = None
        self._poll_retry_delay: RetryDelayFunc | None = None
        self._last_successful_registration: datetime | None = None
        self._tx_fee: TxFee | None = None
        self._timeout_blocks = timeout_blocks

    @property
    def last_successful_registration(self) -> datetime | None:
        return self._last_successful_registration

    @property
    def broadcast_retries(self) -> int | None:
        return self._broadcast_retries

    @broadcast_retries.setter
    def broadcast_retries(self, value: int | None) -> None:
        self._broadcast_retries = value

    @property
    def broadcast_retry_delay(self) -> RetryDelayFunc | None:
        return self._broadcast_retry_delay

    @broadcast_retry_delay.setter
    def broadcast_retry_delay(self, value: RetryDelayFunc | None) -> None:
        self._broadcast_retry_delay = value

    @property
    def poll_retries(self) -> int | None:
        return self._poll_retries

    @poll_retries.setter
    def poll_retries(self, value: int | None) -> None:
        self._poll_retries = value

    @property
    def poll_retry_delay(self) -> RetryDelayFunc | None:
        return self._poll_retry_delay

    @poll_retry_delay.setter
    def poll_retry_delay(self, value: RetryDelayFunc | None) -> None:
        self._poll_retry_delay = value

    def add_agent(self, agent_info: AgentInfo, identity: Identity) -> None:
        agent_record = AlmanacContractRecord(
            address=agent_info.address,
            prefix=agent_info.prefix,
            protocols=agent_info.protocols,
            endpoints=agent_info.endpoints,
            contract_address=str(self._almanac_contract.address),
            sender_address=str(self._wallet.address()),
        )
        self._records.append(agent_record)
        self._identities[agent_info.address] = identity

    def _get_balance(self) -> int:
        return self._ledger.query_bank_balance(Address(self._wallet.address()))

    async def register(self) -> None:
        self._logger.info("Registering agents on Almanac contract...")
        for record in self._records:
            record.sign(self._identities[record.address])

        if self._get_balance() < self._registration_fee * len(self._records):
            self._logger.warning(
                f"I do not have enough funds to register {len(self._records)} "
                "agents on Almanac contract"
            )
            if self._testnet:
                add_testnet_funds(str(self._wallet.address()))
                self._logger.info(f"Adding testnet funds to {self._wallet.address()}")
            else:
                self._logger.info(
                    f"Send funds to wallet address: {self._wallet.address()}"
                )
            raise InsufficientFundsError()

        try:
            await self._almanac_contract.register_batch(
                ledger=self._ledger,
                wallet=self._wallet,
                agent_records=self._records,
                broadcast_retries=self._broadcast_retries,
                broadcast_retry_delay=self._broadcast_retry_delay,
                poll_retries=self._poll_retries,
                poll_retry_delay=self._poll_retry_delay,
                tx_fee=self._tx_fee,
                timeout_blocks=self._timeout_blocks,
            )

            self._logger.info("Registering agents on Almanac contract...complete")
            self._last_successful_registration = datetime.now()

        except RuntimeError as e:
            self._logger.warning(
                "Registering on almanac contract...failed (will retry later)"
            )
            self._logger.debug(e)
        except grpc.RpcError as e:
            self._logger.warning(
                "Registering on almanac contract...failed (will retry later)"
            )
            self._logger.debug(e)


class DefaultRegistrationPolicy(AgentRegistrationPolicy):
    def __init__(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        almanac_contract: AlmanacContract | None,
        testnet: bool,
        *,
        logger: logging.Logger | None = None,
        almanac_api: str | None = None,
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._api_policy = AlmanacApiRegistrationPolicy(
            almanac_api=almanac_api, logger=logger
        )
        if almanac_contract is None:
            self._ledger_policy = None
        else:
            self._ledger_policy = LedgerBasedRegistrationPolicy(
                ledger, wallet, almanac_contract, testnet, logger=logger
            )

    async def register(
        self,
        agent_identifier: str,
        identity: Identity,
        protocols: list[str],
        endpoints: list[AgentEndpoint],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # prefer the API registration policy as it is faster
        try:
            await self._api_policy.register(
                agent_identifier, identity, protocols, endpoints, metadata
            )
        except Exception as e:
            self._logger.warning(
                f"Failed to register on Almanac API: {e.__class__.__name__}"
            )
            self._logger.debug(e)

        if self._ledger_policy is None:
            self._logger.info(
                "No Ledger available. Skipping registration on Almanac contract."
            )
            return

        # schedule the ledger registration
        try:
            await self._ledger_policy.register(
                agent_identifier, identity, protocols, endpoints, metadata
            )
        except InsufficientFundsError:
            self._logger.warning(
                "Failed to register on Almanac contract due to insufficient funds"
            )
            raise
        except Exception as e:
            self._logger.error(
                f"Failed to register on Almanac contract: {e.__class__.__name__}"
            )
            self._logger.debug(e)
            raise


async def update_agent_status(status: AgentStatusUpdate, almanac_api: str):
    _, _, agent_address = parse_identifier(status.agent_identifier)

    with contextlib.suppress(Exception):
        await almanac_api_post(
            url=f"{almanac_api}/agents/{agent_address}/status",
            data=status,
        )


class DefaultBatchRegistrationPolicy(BatchRegistrationPolicy):
    def __init__(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet | None = None,
        almanac_contract: AlmanacContract | None = None,
        testnet: bool = True,
        *,
        logger: logging.Logger | None = None,
        almanac_api: str | None = None,
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._api_policy = BatchAlmanacApiRegistrationPolicy(
            almanac_api=almanac_api, logger=logger
        )

        if almanac_contract is None or wallet is None:
            self._ledger_policy = None
        else:
            self._ledger_policy = BatchLedgerRegistrationPolicy(
                ledger, wallet, almanac_contract, testnet, logger=logger
            )

    def add_agent(self, agent_info: AgentInfo, identity: Identity) -> None:
        self._api_policy.add_agent(agent_info, identity)
        if self._ledger_policy is not None:
            self._ledger_policy.add_agent(agent_info, identity)

    async def register(self) -> None:
        # prefer the API registration policy as it is faster
        try:
            await self._api_policy.register()
        except Exception as e:
            self._logger.warning(
                f"Failed to batch register on Almanac API: {e.__class__.__name__}"
            )
            self._logger.debug(e)

        if self._ledger_policy is None:
            return

        # schedule the ledger registration
        try:
            await self._ledger_policy.register()
        except InsufficientFundsError:
            self._logger.warning(
                "Failed to batch register on Almanac contract due to insufficient funds"
            )
            raise
        except Exception as e:
            self._logger.error(
                f"Failed to batch register on Almanac contract: {e.__class__.__name__}"
            )
            self._logger.debug(e)
            raise
