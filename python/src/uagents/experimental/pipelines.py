from datetime import datetime
from typing import Type

from uagents.context import Context
from uagents.models import Model


class ChainingData(Model):
    sender: str
    created_at: datetime


class SimpleAgentChain:
    def __init__(
        self, target_address: str, request: Type[Model], response: Type[Model]
    ):
        self.target_address = target_address
        self.request_model = request
        self._request_model_digest = Model.build_schema_digest(request)
        self.response_model = response
        self._response_model_digest = Model.build_schema_digest(response)

    async def request(self, ctx: Context, sender: str, request: Model):
        # sanity check: the request model should match
        if Model.build_schema_digest(request) != self._request_model_digest:
            raise ValueError("Unexpected request model")

        # store the sender address
        data = ChainingData(sender=sender, created_at=datetime.now())

        # store the request data into the agent
        storage_key = self._build_storage_key(ctx)
        ctx.storage.set(storage_key, data.model_dump_json())

        # send the request to the target
        await ctx.send(self.target_address, request)

    async def respond(self, ctx: Context, response: Model):
        # sanity check: the response model should match
        if Model.build_schema_digest(response) != self._response_model_digest:
            raise ValueError("Unexpected response model")

        # retrieve the sender address
        storage_key = self._build_storage_key(ctx)

        # retrieve the request data from the agent
        data = ChainingData.model_validate_json(ctx.storage.get(storage_key))

        # send the response to the sender
        await ctx.send(data.sender, response)

        # remove the request data from the agent
        ctx.storage.remove(storage_key)

    def _build_storage_key(self, ctx: Context) -> str:
        if ctx.session is None:
            raise ValueError("Session is missing")

        session = str(ctx.session)
        return f"pipeline/{self._request_model_digest}/{self._response_model_digest}:{session}"
