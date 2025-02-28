import asyncio
import contextlib
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp
import grpc
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.address import Address
from pydantic import AliasChoices, BaseModel, Field

from uagents.config import (
    ALMANAC_API_MAX_RETRIES,
    ALMANAC_API_TIMEOUT_SECONDS,
    ALMANAC_API_URL,
    ALMANAC_CONTRACT_VERSION,
    ALMANAC_REGISTRATION_WAIT,
    REGISTRATION_UPDATE_INTERVAL_SECONDS,
)
from uagents.crypto import Identity
from uagents.network import (
    AlmanacContract,
    AlmanacContractRecord,
    InsufficientFundsError,
    RetryDelayFunc,
    add_testnet_funds,
    default_exp_backoff,
)
from uagents.resolver import parse_identifier
from uagents.types import AgentEndpoint, AgentInfo


class VerifiableModel(BaseModel):
    agent_identifier: str = Field(
        validation_alias=AliasChoices("agent_identifier", "agent_address")
    )
    signature: Optional[str] = None
    timestamp: Optional[int] = None

    def sign(self, identity: Identity):
        self.timestamp = int(time.time())
        digest = self._build_digest()
        self.signature = identity.sign_digest(digest)

    def verify(self) -> bool:
        _, _, agent_address = parse_identifier(self.agent_identifier)
        return self.signature is not None and Identity.verify_digest(
            agent_address, self._build_digest(), self.signature
        )

    def _build_digest(self) -> bytes:
        sha256 = hashlib.sha256()
        sha256.update(
            json.dumps(
                self.model_dump(exclude={"signature"}),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        return sha256.digest()


class AgentRegistrationAttestation(VerifiableModel):
    protocols: List[str]
    endpoints: List[AgentEndpoint]
    metadata: Optional[Dict[str, Union[str, Dict[str, str]]]] = None


class AgentRegistrationAttestationBatch(BaseModel):
    attestations: List[AgentRegistrationAttestation]


class AgentStatusUpdate(VerifiableModel):
    is_active: bool


def coerce_metadata_to_str(
    metadata: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Union[str, Dict[str, str]]]]:
    """
    Step through the metadata and convert any non-string values to strings.
    """
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


def extract_geo_metadata(
    metadata: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Extract geo-location metadata from the metadata dictionary.
    """
    if metadata is None:
        return None
    return {k: v for k, v in metadata.items() if k == "geolocation"}


async def almanac_api_post(
    url: str,
    data: BaseModel,
    *,
    max_retries: Optional[int] = None,
    retry_delay: Optional[RetryDelayFunc] = None,
) -> bool:
    num_retries = max_retries or ALMANAC_API_MAX_RETRIES
    retry_delay_func = retry_delay or default_exp_backoff

    async with aiohttp.ClientSession() as session:
        for retry in range(num_retries):
            try:
                async with session.post(
                    url,
                    headers={"content-type": "application/json"},
                    data=data.model_dump_json(),
                    timeout=aiohttp.ClientTimeout(total=ALMANAC_API_TIMEOUT_SECONDS),
                ) as resp:
                    resp.raise_for_status()
                    return True
            except (aiohttp.ClientError, asyncio.exceptions.TimeoutError) as e:
                if retry + 1 >= num_retries:
                    raise e

                await asyncio.sleep(retry_delay_func(retry))
    return False


class AgentRegistrationPolicy(ABC):
    @abstractmethod
    async def register(
        self,
        agent_identifier: str,
        identity: Identity,
        protocols: List[str],
        endpoints: List[AgentEndpoint],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        pass


class BatchRegistrationPolicy(ABC):
    @abstractmethod
    async def register(self):
        pass

    @abstractmethod
    def add_agent(self, agent_info: AgentInfo, identity: Identity):
        pass


class AlmanacApiRegistrationPolicy(AgentRegistrationPolicy):
    def __init__(
        self,
        *,
        almanac_api: Optional[str] = None,
        max_retries: int = ALMANAC_API_MAX_RETRIES,
        retry_delay: Optional[RetryDelayFunc] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._almanac_api = almanac_api or ALMANAC_API_URL
        self._max_retries = max_retries
        self._logger = logger or logging.getLogger(__name__)
        self._retry_delay = retry_delay or default_exp_backoff
        self._last_successful_registration: Optional[datetime] = None

    @property
    def last_successful_registration(self) -> Optional[datetime]:
        return self._last_successful_registration

    async def register(
        self,
        agent_identifier: str,
        identity: Identity,
        protocols: List[str],
        endpoints: List[AgentEndpoint],
        metadata: Optional[Dict[str, Any]] = None,
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
                f"{self._almanac_api}/agents",
                attestation,
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
        almanac_api: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        max_retries: int = ALMANAC_API_MAX_RETRIES,
        retry_delay: Optional[RetryDelayFunc] = None,
    ):
        self._almanac_api = almanac_api or ALMANAC_API_URL
        self._attestations: List[AgentRegistrationAttestation] = []
        self._logger = logger or logging.getLogger(__name__)
        self._max_retries = max_retries
        self._retry_delay = retry_delay or default_exp_backoff
        self._last_successful_registration: Optional[datetime] = None

    @property
    def last_successful_registration(self) -> Optional[datetime]:
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
                f"{self._almanac_api}/agents/batch",
                attestations,
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
        logger: Optional[logging.Logger] = None,
    ):
        self._wallet = wallet
        self._ledger = ledger
        self._testnet = testnet
        self._almanac_contract = almanac_contract
        self._registration_fee = almanac_contract.get_registration_fee()
        self._logger = logger or logging.getLogger(__name__)
        self._broadcast_retries: Optional[int] = None
        self._broadcast_retry_delay: Optional[RetryDelayFunc] = None
        self._poll_retries: Optional[int] = None
        self._poll_retry_delay: Optional[RetryDelayFunc] = None
        self._last_successful_registration: Optional[datetime] = None

    @property
    def last_successful_registration(self) -> Optional[datetime]:
        return self._last_successful_registration

    @property
    def broadcast_retries(self) -> Optional[int]:
        return self._broadcast_retries

    @broadcast_retries.setter
    def broadcast_retries(self, value: Optional[int]):
        self._broadcast_retries = value

    @property
    def broadcast_retry_delay(self) -> Optional[RetryDelayFunc]:
        return self._broadcast_retry_delay

    @broadcast_retry_delay.setter
    def broadcast_retry_delay(self, value: Optional[RetryDelayFunc]):
        self._broadcast_retry_delay = value

    @property
    def poll_retries(self) -> Optional[int]:
        return self._poll_retries

    @poll_retries.setter
    def poll_retries(self, value: Optional[int]):
        self._poll_retries = value

    @property
    def poll_retry_delay(self) -> Optional[RetryDelayFunc]:
        return self._poll_retry_delay

    @poll_retry_delay.setter
    def poll_retry_delay(self, value: Optional[RetryDelayFunc]):
        self._poll_retry_delay = value

    def check_contract_version(self):
        """
        Check the version of the deployed Almanac contract and log a warning
        if it is different from the supported version.
        """
        deployed_version = self._almanac_contract.get_contract_version()
        if deployed_version != ALMANAC_CONTRACT_VERSION:
            self._logger.warning(
                "Mismatch in almanac contract versions: supported (%s), deployed (%s). "
                "Update uAgents to the latest version for compatibility.",
                ALMANAC_CONTRACT_VERSION,
                deployed_version,
            )

    async def register(
        self,
        agent_identifier: str,
        identity: Identity,
        protocols: List[str],
        endpoints: List[AgentEndpoint],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Register the agent on the Almanac contract if registration is about to expire or
        the registration data has changed.
        """
        self.check_contract_version()

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
                    self._ledger,
                    self._wallet,
                    agent_address,
                    protocols,
                    endpoints,
                    signature,
                    current_time,
                    broadcast_retries=self._broadcast_retries,
                    broadcast_retry_delay=self._broadcast_retry_delay,
                    poll_retries=self._poll_retries,
                    poll_retry_delay=self._poll_retry_delay,
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
        return identity.sign_registration(
            str(self._almanac_contract.address),
            timestamp,
            str(self._wallet.address()),
        )


class BatchLedgerRegistrationPolicy(BatchRegistrationPolicy):
    def __init__(
        self,
        ledger: LedgerClient,
        wallet: LocalWallet,
        almanac_contract: AlmanacContract,
        testnet: bool,
        logger: Optional[logging.Logger] = None,
    ):
        self._ledger = ledger
        self._wallet = wallet
        self._almanac_contract = almanac_contract
        self._testnet = testnet
        self._registration_fee = almanac_contract.get_registration_fee()
        self._logger = logger or logging.getLogger(__name__)
        self._records: List[AlmanacContractRecord] = []
        self._identities: Dict[str, Identity] = {}

        self._broadcast_retries: Optional[int] = None
        self._broadcast_retry_delay: Optional[RetryDelayFunc] = None
        self._poll_retries: Optional[int] = None
        self._poll_retry_delay: Optional[RetryDelayFunc] = None
        self._last_successful_registration: Optional[datetime] = None

    @property
    def last_successful_registration(self) -> Optional[datetime]:
        return self._last_successful_registration

    @property
    def broadcast_retries(self) -> Optional[int]:
        return self._broadcast_retries

    @broadcast_retries.setter
    def broadcast_retries(self, value: Optional[int]):
        self._broadcast_retries = value

    @property
    def broadcast_retry_delay(self) -> Optional[RetryDelayFunc]:
        return self._broadcast_retry_delay

    @broadcast_retry_delay.setter
    def broadcast_retry_delay(self, value: Optional[RetryDelayFunc]):
        self._broadcast_retry_delay = value

    @property
    def poll_retries(self) -> Optional[int]:
        return self._poll_retries

    @poll_retries.setter
    def poll_retries(self, value: Optional[int]):
        self._poll_retries = value

    @property
    def poll_retry_delay(self) -> Optional[RetryDelayFunc]:
        return self._poll_retry_delay

    @poll_retry_delay.setter
    def poll_retry_delay(self, value: Optional[RetryDelayFunc]):
        self._poll_retry_delay = value

    def add_agent(self, agent_info: AgentInfo, identity: Identity):
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

    async def register(self):
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
                self._ledger,
                self._wallet,
                self._records,
                broadcast_retries=self._broadcast_retries,
                broadcast_retry_delay=self._broadcast_retry_delay,
                poll_retries=self._poll_retries,
                poll_retry_delay=self._poll_retry_delay,
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
        almanac_contract: Optional[AlmanacContract],
        testnet: bool,
        *,
        logger: Optional[logging.Logger] = None,
        almanac_api: Optional[str] = None,
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
        protocols: List[str],
        endpoints: List[AgentEndpoint],
        metadata: Optional[Dict[str, Any]] = None,
    ):
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
            f"{almanac_api}/agents/{agent_address}/status",
            status,
        )


class DefaultBatchRegistrationPolicy(BatchRegistrationPolicy):
    def __init__(
        self,
        ledger: LedgerClient,
        wallet: Optional[LocalWallet] = None,
        almanac_contract: Optional[AlmanacContract] = None,
        testnet: bool = True,
        *,
        logger: Optional[logging.Logger] = None,
        almanac_api: Optional[str] = None,
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

    def add_agent(self, agent_info: AgentInfo, identity: Identity):
        self._api_policy.add_agent(agent_info, identity)
        if self._ledger_policy is not None:
            self._ledger_policy.add_agent(agent_info, identity)

    async def register(self):
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
