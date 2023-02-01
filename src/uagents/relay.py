import asyncio
import json
import logging

import aiohttp

from uagents.config import RELAY_POLL_INTERVAL_SECONDS
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope


class RelayClient:
    def __init__(self, agent, server_url: str):
        self._server_url = server_url
        self._agent = agent
        self._access_token: str = None
        self._poll_interval = RELAY_POLL_INTERVAL_SECONDS

    async def run(self):
        while True:
            if self._access_token is None:
                await self._get_access_token()
            await self._poll_server()
            await asyncio.sleep(self._poll_interval)

    async def _poll_server(self):
        async with aiohttp.ClientSession() as session:
            mailbox_url = f"{self._server_url}/v1/mailbox"
            async with session.get(
                mailbox_url,
                headers={"Authorization": f"token {self._access_token}"},
            ) as resp:
                success = resp.status == 200
                if success:
                    items = (await resp.json())["items"]
                    for item in items:
                        env = Envelope.parse_obj(item["envelope"])
                        if env.verify():
                            await dispatcher.dispatch(
                                env.sender,
                                env.target,
                                env.protocol,
                                env.decode_payload(),
                            )
                else:
                    logging.exception(
                        f"Failed to retrieve messages from inbox: {(await resp.text())}"
                    )

            if success and len(items) > 0:
                async with session.delete(
                    mailbox_url,
                    headers={"Authorization": f"token {self._access_token}"},
                ) as resp:
                    if resp.status != 200:
                        logging.warning("Failed to delete messages from inbox")

    async def _get_access_token(self):
        async with aiohttp.ClientSession() as session:

            # get challenge
            challenge_url = f"{self._server_url}/v1/auth/challenge"
            async with session.post(
                challenge_url,
                data=json.dumps({"address": self._agent.address}),
                headers={"content-type": "application/json"},
            ) as resp:
                if resp and resp.status == 200:
                    challenge: str = (await resp.json())["challenge"]
                else:
                    logging.exception(
                        f"Failed to retrieve authorization challenge: {(await resp.text())}"
                    )
                    return

            # response to challenge with signature to get token
            prove_url = f"{self._server_url}/v1/auth/prove"
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
                    logging.exception(
                        f"Failed to prove authorization: {(await resp.text())}"
                    )
