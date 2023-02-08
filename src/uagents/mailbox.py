import asyncio
import json
import logging
from typing import Dict, Optional

import aiohttp
import pydantic
from aiohttp.client_exceptions import ClientConnectorError

from uagents.config import get_logger, MAILBOX_POLL_INTERVAL_SECONDS
from uagents.crypto import is_user_address
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope


class MailboxClient:
    def __init__(
        self, agent, config: Dict[str, str], logger: Optional[logging.Logger] = None
    ):
        self._base_url = config["base_url"]
        self._api_key = config["api_key"]
        self._agent = agent
        self._access_token: str = None
        self._poll_interval = MAILBOX_POLL_INTERVAL_SECONDS
        self._logger = logger or get_logger("mailbox")

    async def run(self):
        self._logger.info(f"Connecting to mailbox server at {self._base_url}")
        while True:
            try:
                if self._access_token is None:
                    await self._get_access_token()
                await self._poll_server()
            except ClientConnectorError:
                self._logger.exception("Failed to connect to mailbox server")
            await asyncio.sleep(self._poll_interval)

    async def _poll_server(self):
        async with aiohttp.ClientSession() as session:

            # check the inbox for envelopes and dispatch them
            mailbox_url = f"{self._base_url}/v1/mailbox"
            async with session.get(
                mailbox_url,
                headers={"Authorization": f"token {self._access_token}"},
            ) as resp:
                success = resp.status == 200
                if success:
                    items = (await resp.json())["items"]
                    for item in items:
                        try:
                            env = Envelope.parse_obj(item["envelope"])
                        except pydantic.ValidationError:
                            self._logger.warning("Received invalid envelope")
                            continue

                        do_verify = not is_user_address(env.sender)

                        if do_verify and env.verify() is False:
                            self._logger.warning(
                                "Received envelope that failed verification"
                            )
                            continue

                        if not dispatcher.contains(env.target):
                            self._logger.warning(
                                "Received envelope for unrecognized address"
                            )
                            continue

                        await dispatcher.dispatch(
                            env.sender,
                            env.target,
                            env.protocol,
                            env.decode_payload(),
                        )
                else:
                    self._logger.exception(
                        f"Failed to retrieve messages from inbox: {(await resp.text())}"
                    )

            # delete any envelopes that were successfully processed
            if success and len(items) > 0:
                for item in items:
                    env_url = f"{self._base_url}/v1/mailbox/{item['uuid']}"
                    async with session.delete(
                        env_url,
                        headers={"Authorization": f"token {self._access_token}"},
                    ) as resp:
                        if resp.status != 200:
                            self._logger.exception(
                                f"Failed to delete envelope from inbox: {(await resp.text())}"
                            )

    async def _get_access_token(self):
        async with aiohttp.ClientSession() as session:

            # get challenge
            challenge_url = f"{self._base_url}/v1/auth/challenge"
            async with session.post(
                challenge_url,
                data=json.dumps({"address": self._agent.address}),
                headers={"content-type": "application/json"},
            ) as resp:
                if resp and resp.status == 200:
                    challenge: str = (await resp.json())["challenge"]
                else:
                    self._logger.exception(
                        f"Failed to retrieve authorization challenge: {(await resp.text())}"
                    )
                    return

            # response to challenge with signature to get token
            prove_url = f"{self._base_url}/v1/auth/prove"
            async with session.post(
                prove_url,
                data=json.dumps(
                    {
                        "address": self._agent.address,
                        "challenge": challenge,
                        "challenge_response": self._agent.sign(challenge.encode()),
                    }
                ),
                headers={"content-type": "application/json"},
            ) as resp:
                if resp and resp.status == 200:
                    self._access_token = (await resp.json())["access_token"]
                else:
                    self._logger.exception(
                        f"Failed to prove authorization: {(await resp.text())}"
                    )
