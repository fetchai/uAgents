import asyncio
import base64
import functools
import logging
from typing import List, Optional

from babble import (  # pylint: disable=unused-import
    Client,
    Identity as BabbleIdentity,
    Message as WalletMessage,
)
from cosmpy.aerial.wallet import LocalWallet
from requests import HTTPError, JSONDecodeError

from uagents.config import (
    WALLET_MESSAGING_POLL_INTERVAL_SECONDS,
    get_logger,
)
from uagents.context import Context, WalletMessageCallback
from uagents.crypto import Identity


class WalletMessagingClient:
    def __init__(
        self,
        identity: Identity,
        wallet: LocalWallet,
        chain_id: str,
        logger: Optional[logging.Logger] = None,
    ):
        delegate_pubkey = identity.pub_key
        delegate_pubkey_b64 = base64.b64encode(bytes.fromhex(delegate_pubkey)).decode()
        public_key = base64.b64decode(wallet.public_key().public_key).hex()
        signed_bytes, signature = identity.sign_arbitrary(public_key.encode())
        self._client = Client(
            identity.address,
            delegate_pubkey_b64,
            signature,
            signed_bytes,
            BabbleIdentity(wallet.signer().private_key_bytes),
            chain_id,
        )
        self._poll_interval = WALLET_MESSAGING_POLL_INTERVAL_SECONDS
        self._logger = logger or get_logger("wallet_messaging")
        self._message_queue = asyncio.Queue()
        self._message_handlers: List[WalletMessageCallback] = []

    def on_message(
        self,
    ):
        def decorator_on_message(func: WalletMessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._message_handlers.append(func)

            return handler

        return decorator_on_message

    async def send(self, destination: str, msg: str, msg_type: int = 1):
        try:
            self._client.send(destination, msg, msg_type)
        except Exception as ex:
            self._logger.exception(f"Failed to send message to {destination}: {ex}")

    async def poll_server(self):
        self._logger.info("Connecting to wallet messaging server")
        while True:
            try:
                for msg in self._client.receive():
                    await self._message_queue.put(msg)
            except (
                HTTPError,
                ConnectionError,
                JSONDecodeError,
                Exception,
            ) as ex:
                self._logger.warning(
                    f"Failed to get messages from wallet messaging server: {ex}"
                )
            await asyncio.sleep(self._poll_interval)

    async def process_message_queue(self, ctx: Context):
        while True:
            msg = await self._message_queue.get()
            for handler in self._message_handlers:
                await handler(ctx, msg)
