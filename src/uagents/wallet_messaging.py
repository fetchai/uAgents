import asyncio
import functools
import logging
from typing import List, Optional

from babble import Client, Identity as BabbleIdentity
from babble.client import Message as WalletMessage
from cosmpy.aerial.wallet import LocalWallet

from uagents.config import WALLET_MESSAGING_POLL_INTERVAL_SECONDS, get_logger
from uagents.context import Context, WalletMessageCallback


class WalletMessagingClient:
    def __init__(
        self,
        delegate_address: str,
        wallet: LocalWallet,
        logger: Optional[logging.Logger] = None,
    ):
        self._client = Client(
            delegate_address,
            BabbleIdentity(wallet.signer().private_key_bytes),
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

    async def send(self, destination: str, msg: WalletMessage):
        self._client.send(destination, msg)

    async def poll_server(self):
        self._logger.info(f"Connecting to wallet messaging server")
        while True:
            for msg in self._client.receive():
                await self._message_queue.put(msg)
            await asyncio.sleep(self._poll_interval)

    async def process_message_queue(self, ctx: Context):
        while True:
            msg = await self._message_queue.get()
            for handler in self._message_handlers:
                await handler(ctx, msg)
