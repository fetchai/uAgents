import asyncio
import json
import logging
from typing import Optional

import aiohttp
import pydantic
from aiohttp.client_exceptions import ClientConnectorError
from websockets import connect
import websockets.exceptions

from uagents.config import get_logger, MAILBOX_POLL_INTERVAL_SECONDS
from uagents.crypto import is_user_address
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope


class MailboxClient:
    def __init__(self, agent, logger: Optional[logging.Logger] = None):
        self._agent = agent
        self._access_token: Optional[str] = None
        self._envelopes_to_delete = asyncio.Queue()
        self._poll_interval = MAILBOX_POLL_INTERVAL_SECONDS
        self._logger = logger or get_logger("mailbox")

    @property
    def base_url(self):
        return self._agent.mailbox["base_url"]

    @property
    def api_key(self):
        return self._agent.mailbox["api_key"]

    @property
    def protocol(self):
        return self._agent.mailbox["protocol"]

    @property
    def http_prefix(self):
        return self._agent.mailbox["http_prefix"]

    async def run(self):
        self._logger.info(f"Connecting to mailbox server at {self.base_url}")
        while True:
            try:
                if self._access_token is None:
                    await self._get_access_token()
                if self.protocol in {"ws", "wss"}:
                    await self._open_websocket_connection()
                else:
                    await self._poll_server()
                    await asyncio.sleep(self._poll_interval)
            except ClientConnectorError:
                self._logger.exception("Failed to connect to mailbox server")

    async def _handle_envelope(self, payload: dict):
        try:
            env = Envelope.parse_obj(payload["envelope"])
        except pydantic.ValidationError:
            self._logger.warning("Received invalid envelope")
            return

        do_verify = not is_user_address(env.sender)

        if do_verify and env.verify() is False:
            self._logger.warning("Received envelope that failed verification")
            return

        if not dispatcher.contains(env.target):
            self._logger.warning("Received envelope for unrecognized address")
            return

        await dispatcher.dispatch(
            env.sender,
            env.target,
            env.protocol,
            env.decode_payload(),
        )

        # queue envelope for deletion from server
        await self._envelopes_to_delete.put(payload)

    async def process_deletion_queue(self):
        async with aiohttp.ClientSession() as session:
            while True:
                env_payload = await self._envelopes_to_delete.get()
                env_url = f"{self.http_prefix}://{self.base_url}/v1/mailbox/{env_payload['uuid']}"
                self._logger.debug(f"Deleting message: {env_payload}")
                async with session.delete(
                    env_url,
                    headers={"Authorization": f"token {self._access_token}"},
                ) as resp:
                    if resp.status != 200:
                        self._logger.exception(
                            f"Failed to delete envelope from inbox: {(await resp.text())}"
                        )

    async def _poll_server(self):
        async with aiohttp.ClientSession() as session:
            # check the inbox for envelopes and handle them
            mailbox_url = f"{self.http_prefix}://{self.base_url}/v1/mailbox"
            async with session.get(
                mailbox_url,
                headers={"Authorization": f"token {self._access_token}"},
            ) as resp:
                success = resp.status == 200
                if success:
                    items = (await resp.json())["items"]
                    for item in items:
                        await self._handle_envelope(item)
                elif resp.status == 401:
                    self._access_token = None
                    self._logger.warning(
                        "Access token expired: a new one should be retrieved automatically"
                    )
                else:
                    self._logger.exception(
                        f"Failed to retrieve messages: {resp.status}:{(await resp.text())}"
                    )

    async def _open_websocket_connection(self):
        try:
            async with connect(
                f"{self.protocol}://{self.base_url}/v1/events?token={self._access_token}"
            ) as websocket:
                # wait for the event stream to come in
                while True:
                    msg = await websocket.recv()
                    msg = json.loads(msg)
                    if msg["type"] == "envelope":
                        self._logger.debug(f"Got envelope: {msg['payload']}")
                        await self._handle_envelope(msg["payload"])

        except websockets.exceptions.ConnectionClosedError:
            pass

        except ConnectionRefusedError:
            pass

    async def _get_access_token(self):
        async with aiohttp.ClientSession() as session:
            # get challenge
            challenge_url = f"{self.http_prefix}://{self.base_url}/v1/auth/challenge"
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
            prove_url = f"{self.http_prefix}://{self.base_url}/v1/auth/prove"
            async with session.post(
                prove_url,
                data=json.dumps(
                    {
                        "address": self._agent.address,
                        "api_key": self.api_key,
                        "challenge": challenge,
                        "challenge_response": self._agent.sign(challenge.encode()),
                    }
                ),
                headers={"content-type": "application/json"},
            ) as resp:
                if resp and resp.status == 200:
                    self._logger.info("Mailbox access token acquired")
                    self._access_token = (await resp.json())["access_token"]
                else:
                    self._logger.exception(
                        f"Failed to prove authorization: {(await resp.text())}"
                    )
