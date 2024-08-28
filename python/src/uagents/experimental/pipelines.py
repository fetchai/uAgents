import asyncio
from datetime import datetime
from typing import Type, Literal

from uagents.context import Context
from uagents.models import Model


class ChainingData(Model):
    sender: str
    created_at: datetime


class Pipeline:
    @staticmethod
    def all(requests: list[tuple[str, Type[Model], Type[Model]]]):
        return Pipeline("all", requests)

    @staticmethod
    def first(requests: list[tuple[str, Type[Model], Type[Model]]]):
        return Pipeline("first", requests)

    def __init__(self, mode: Literal["all", "first", "last"], requests: list[tuple[str, Type[Model], Type[Model]]]):
        self._handler = None
        self._mode = mode
        self._total_expected = len(requests)

        # build the set of expected responses from each sender and store the index order
        self._expected_requests: dict[str, set[str]] = {}
        self._expected_responses: dict[str, dict[str, int]] = {}
        for idx, (sender, request_model, response_model) in enumerate(requests):
            request_model_digest = Model.build_schema_digest(request_model)
            response_model_digest = Model.build_schema_digest(response_model)

            self._expected_requests.setdefault(sender, set()).add(request_model_digest)
            self._expected_responses.setdefault(sender, dict()).setdefault(response_model_digest, idx)

        # set up the store of all the messages received
        self._queued: dict[str, list[tuple[str, Model] | None]] = {}
        self._completed: dict[str, asyncio.Future] = {}

    async def handle(self, ctx: Context, sender: str, response: Model):
        print(ctx.session, sender, response)

        index = self._get_response_index(sender, response)
        if index < 0:
            ctx.logger.warning(f"Unexpected response from {sender}")
            return

        # create a new set of records if the session is new
        session_id = str(ctx.session)
        if session_id not in self._queued:
            current_session = [None] * self._total_expected # type: list[tuple[str, Model] | None]
        else:
            current_session = self._queued[session_id] # type: list[tuple[str, Model] | None]

        # sanity check: we should not have duplicate responses
        if current_session[index] is not None:
            ctx.logger.warning(f"Duplicate response from {sender}")
            return

        # update the current session with the response
        current_session[index] = (sender, response)

        # count the total number of responses received
        total_received = sum(1 for item in current_session if item is not None)

        # update the current session
        self._queued[session_id] = current_session

        # check if we are done
        if self._mode == "all":
            complete = total_received == self._total_expected
        elif self._mode == "first":
            complete = total_received > 0
        else:
            raise ValueError("Invalid mode")

        # dispatch the responses to the handler if we are done
        if complete:

            # lookup the future
            future = self._completed.get(session_id)
            if future is not None:

                # update the result
                future.set_result(current_session)

                # clean up the session data
                del self._queued[session_id]
                del self._completed[session_id]

    async def scatter_and_gather(self, ctx: Context, requests: list[tuple[str, Model]]):
        session_id = str(ctx.session)
        if session_id in self._completed:
            raise ValueError("Session is already in progress")

        # validate the requests
        for receiver, request in requests:
            request_digest = Model.build_schema_digest(request)
            if request_digest not in self._expected_requests.get(receiver, set()):
                raise ValueError(f"Unexpected request for {receiver}")

        # create a new future for the session
        future = asyncio.get_event_loop().create_future()
        self._completed[session_id] = future

        # send all the requests (the scatter part)
        await asyncio.gather(*[ctx.send(sender, request) for sender, request in requests])

        # wait for the future to complete (the gather part)
        return await future

    def _get_response_index(self, sender: str, model: Model) -> int:
        model_digest = Model.build_schema_digest(model)
        return self._expected_responses.get(sender, dict()).get(model_digest, -1)

    # def on_complete(self):
    #     def decorator_on_complete(func: Callable[[Context, list[tuple[str, Model]]], Awaitable[None]]):
    #         @functools.wraps(func)
    #         def handler(*args, **kwargs):
    #             return func(*args, **kwargs)
    #
    #         self._handler = handler
    #         return handler
    #
    #     return decorator_on_complete


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
