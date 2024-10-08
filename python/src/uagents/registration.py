import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

import aiohttp
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.address import Address
from pydantic import BaseModel

from uagents.config import (
    ALMANAC_API_MAX_RETRIES,
    ALMANAC_API_TIMEOUT_SECONDS,
    ALMANAC_API_URL,
    REGISTRATION_FEE,
    REGISTRATION_UPDATE_INTERVAL_SECONDS,
)
from uagents.crypto import Identity
from uagents.network import AlmanacContract, InsufficientFundsError, add_testnet_funds
from uagents.types import AgentEndpoint


class AgentRegistrationPolicy(ABC):
    @abstractmethod
    # pylint: disable=unnecessary-pass
    async def register(
        self, agent_address: str, protocols: List[str], endpoints: List[AgentEndpoint]
    ):
        pass


class AgentGeoLocation(BaseModel):
    # Latitude and longitude of the agent
    latitude: float
    longitude: float

    # Radius around the agent location, expressed in meters
    radius: float


class AgentRegistrationAttestation(BaseModel):
    agent_address: str
    protocols: List[str]
    endpoints: List[AgentEndpoint]
    signature: Optional[str] = None
    location: Optional[AgentGeoLocation] = None

    def sign(self, identity: Identity):
        digest = self._build_digest()
        self.signature = identity.sign_digest(digest)

    def verify(self) -> bool:
        if self.signature is None:
            raise ValueError("Attestation signature is missing")
        return Identity.verify_digest(
            self.agent_address, self._build_digest(), self.signature
        )

    def _build_digest(self) -> bytes:
        normalised_attestation = AgentRegistrationAttestation(
            agent_address=self.agent_address,
            protocols=sorted(self.protocols),
            endpoints=sorted(self.endpoints, key=lambda x: x.url),
        )

        sha256 = hashlib.sha256()
        sha256.update(
            json.dumps(
                normalised_attestation.model_dump(exclude={"signature"}),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        return sha256.digest()


class AlmanacApiRegistrationPolicy(AgentRegistrationPolicy):
    def __init__(
        self,
        identity: Identity,
        *,
        almanac_api: Optional[str] = None,
        max_retries: int = ALMANAC_API_MAX_RETRIES,
        logger: Optional[logging.Logger] = None,
    ):
        self._almanac_api = almanac_api or ALMANAC_API_URL
        self._max_retries = max_retries
        self._identity = identity
        self._logger = logger or logging.getLogger(__name__)

    async def register(
        self, agent_address: str, protocols: List[str], endpoints: List[AgentEndpoint]
    ):
        # create the attestation
        attestation = AgentRegistrationAttestation(
            agent_address=agent_address, protocols=protocols, endpoints=endpoints
        )

        # sign the attestation
        attestation.sign(self._identity)

        # submit the attestation to the API
        async with aiohttp.ClientSession() as session:  # noqa: SIM117
            for retry in range(self._max_retries):
                try:
                    async with session.post(
                        f"{self._almanac_api}/agents",
                        headers={"content-type": "application/json"},
                        data=attestation.model_dump_json(),
                        timeout=ALMANAC_API_TIMEOUT_SECONDS,
                    ) as resp:
                        resp.raise_for_status()
                        self._logger.info("Registration on Almanac API successful")
                        return
                except (aiohttp.ClientError, asyncio.exceptions.TimeoutError) as e:
                    if retry == self._max_retries - 1:
                        raise e

                    # generate a backoff time starting from 0.128 seconds and limited
                    # to ~131 seconds
                    backoff = (2 ** (min(retry, 11) + 6)) / 1000
                    await asyncio.sleep(backoff)


class LedgerBasedRegistrationPolicy(AgentRegistrationPolicy):
    def __init__(
        self,
        identity: Identity,
        ledger: LedgerClient,
        wallet: LocalWallet,
        almanac_contract: AlmanacContract,
        testnet: bool,
        *,
        logger: Optional[logging.Logger] = None,
    ):
        self._identity = identity
        self._wallet = wallet
        self._ledger = ledger
        self._testnet = testnet
        self._almanac_contract = almanac_contract
        self._logger = logger or logging.getLogger(__name__)

    async def register(
        self, agent_address: str, protocols: List[str], endpoints: List[AgentEndpoint]
    ):
        # register if not yet registered or registration is about to expire
        # or anything has changed from the last registration
        if (
            not self._almanac_contract.is_registered(agent_address)
            or self._almanac_contract.get_expiry(agent_address)
            < REGISTRATION_UPDATE_INTERVAL_SECONDS
            or endpoints != self._almanac_contract.get_endpoints(agent_address)
            or protocols != self._almanac_contract.get_protocols(agent_address)
        ):
            if self._get_balance() < REGISTRATION_FEE:
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

            signature = self._sign_registration(agent_address)
            await self._almanac_contract.register(
                self._ledger,
                self._wallet,
                agent_address,
                protocols,
                endpoints,
                signature,
            )
            self._logger.info("Registering on almanac contract...complete")
        else:
            self._logger.info("Almanac contract registration is up to date!")

    def _get_balance(self) -> int:
        return self._ledger.query_bank_balance(Address(self._wallet.address()))

    def _sign_registration(self, agent_address: str) -> str:
        """
        Sign the registration data for Almanac contract.

        Returns:
            str: The signature of the registration data.

        Raises:
            AssertionError: If the Almanac contract address is None.

        """
        assert self._almanac_contract.address is not None
        return self._identity.sign_registration(
            str(self._almanac_contract.address),
            self._almanac_contract.get_sequence(agent_address),
        )


class DefaultRegistrationPolicy(AgentRegistrationPolicy):
    def __init__(
        self,
        identity: Identity,
        ledger: LedgerClient,
        wallet: LocalWallet,
        almanac_contract: AlmanacContract,
        testnet: bool,
        *,
        logger: Optional[logging.Logger] = None,
        almanac_api: Optional[str] = None,
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._api_policy = AlmanacApiRegistrationPolicy(
            identity, almanac_api=almanac_api, logger=logger
        )
        self._ledger_policy = LedgerBasedRegistrationPolicy(
            identity, ledger, wallet, almanac_contract, testnet, logger=logger
        )

    async def register(
        self,
        agent_address: str,
        protocols: List[str],
        endpoints: List[AgentEndpoint],
    ):
        # prefer the API registration policy as it is faster
        try:
            await self._api_policy.register(agent_address, protocols, endpoints)
        except Exception as e:
            self._logger.warning(
                f"Failed to register on Almanac API: {e.__class__.__name__}"
            )

        # schedule the ledger registration
        try:
            await self._ledger_policy.register(agent_address, protocols, endpoints)
        except InsufficientFundsError:
            self._logger.warning(
                "Failed to register on Almanac contract due to insufficient funds"
            )
            raise
        except Exception as e:
            self._logger.error(f"Failed to register on Almanac contract: {e}")
            raise
