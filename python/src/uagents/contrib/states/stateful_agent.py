import asyncio
import functools
from typing import Dict, Optional, Set, Type, Union

from pydantic import ValidationError
from uagents.agent import Agent, _send_error_message
from uagents.context import Context, IntervalCallback, MessageCallback, MsgDigest
from uagents.crypto import is_user_address
from uagents.models import ErrorMessage, Model
from uagents.protocol import Protocol


class StatefulAgentProtocol(Protocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state_message_handlers: Dict[str, tuple[MessageCallback, str]] = {}

    @property
    def state_message_handlers(self):
        """
        Property to access the state message handlers.

        Returns:
            Dict[str, tuple[MessageCallback, str]]: Dictionary mapping message schema digests to their handlers and states.
        """  # noqa
        return self._state_message_handlers

    def on_interval(
        self,
        period: float,
        messages: type[Model] | Set[type[Model]] | None = None,
        state: Optional[str] = None,
    ):
        """code changed from original"""

        def decorator_on_interval(func: IntervalCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._add_state_interval_handler(period, func, messages, state)

            return handler

        return decorator_on_interval

    def _add_state_interval_handler(
        self,
        period: float,
        func: IntervalCallback,
        messages: Optional[Union[Type[Model], Set[Type[Model]]]],
        state: Optional[str] = None,
    ):
        # add state to interval handlers
        self._interval_handlers.append((func, period, state))

        # if message types are specified, store these for validation
        if messages is not None:
            if not isinstance(messages, set):
                messages = {messages}
            for message in messages:
                message_digest = Model.build_schema_digest(message)
                self._interval_messages.add(message_digest)

    def on_message(
        self,
        model: Model,
        replies: type[Model] | Set[type[Model]] | None = None,
        allow_unverified: bool | None = False,
        state: Optional[str] = None,
    ):
        """code changed from original"""

        def decorator_on_message(func):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._add_state_message_handler(
                model, func, replies, allow_unverified, state
            )

            return handler

        return decorator_on_message

    def _add_state_message_handler(
        self,
        model: Type[Model],
        func: MessageCallback,
        replies: Optional[Union[Type[Model], Set[Type[Model]]]],
        allow_unverified: Optional[bool] = False,
        state: Optional[str] = None,
    ):
        """
        Add a message handler to the protocol.

        Args:
            model (Type[Model]): The message model type.
            func (MessageCallback): The message handler function.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]]): The associated reply types.
            allow_unverified (Optional[bool], optional): Whether to allow unverified messages.
            Defaults to False.
        """
        model_digest = Model.build_schema_digest(model)

        # update the model database
        self._models[model_digest] = model
        if allow_unverified:
            self._unsigned_message_handlers[model_digest] = func
        elif state is not None:
            self._state_message_handlers[model_digest] = (func, state)
        else:
            self._signed_message_handlers[model_digest] = func
        if replies is not None:
            if not isinstance(replies, set):
                replies = {replies}
            self._replies[model_digest] = {
                Model.build_schema_digest(reply): reply for reply in replies
            }


async def _run_interval(
    func: IntervalCallback,
    state: Optional[str],  # desired state
    ctx: Context,
    period: float,
):
    """
    Run the provided interval callback function at a specified period.

    Args:
        func (IntervalCallback): The interval callback function to run.
        ctx (Context): The context for the agent.
        period (float): The time period at which to run the callback function.
    """
    while True:
        try:
            if ctx.state == state or state is None:
                await func(ctx)
        except OSError as ex:
            ctx.logger.exception(f"OS Error in interval handler: {ex}")
        except RuntimeError as ex:
            ctx.logger.exception(f"Runtime Error in interval handler: {ex}")
        except Exception as ex:
            ctx.logger.exception(f"Exception in interval handler: {ex}")

        await asyncio.sleep(period)


class StatefulContext(Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = None

    @property
    def state(self):
        """
        Get the state of the context

        Returns:
            str: The state of the context
        """
        return self._state

    @state.setter
    def state(self, state: Optional[str]):
        """
        Set the state of the context

        Args:
            state (str): The state to set
        """
        self._state = state


class StatefulAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ctx = StatefulContext(
            self._identity.address,
            self.identifier,
            self._name,
            self._storage,
            self._resolver,
            self._identity,
            self._wallet,
            self._ledger,
            self._queries,
            replies=self._replies,
            interval_messages=self._interval_messages,
            wallet_messaging_client=self._wallet_messaging_client,
            protocols=self.protocols,
            logger=self._logger,
        )
        self._protocol = StatefulAgentProtocol(name=self._name, version=self._version)
        self._state_message_handlers: Dict[str, tuple[MessageCallback, str]] = {}

    @property
    def state(self):
        """
        Get the state of the agent

        Returns:
            str: The state of the agent
        """
        return self._ctx.state or None

    @state.setter
    def state(self, state: Optional[str]):
        """
        Set the state of the agent

        Args:
            state (str): The state to set
        """
        self._ctx.state = state

    # interval handling
    def on_interval(
        self,
        period: float,
        messages: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        state: Optional[str] = None,
    ):
        return self._protocol.on_interval(period, messages, state)

    def include(self, protocol: Protocol, publish_manifest: Optional[bool] = False):
        for func, period, state in protocol.intervals:
            self._interval_handlers.append((func, period, state))

        self._interval_messages.update(protocol.interval_messages)

        for schema_digest in protocol.models:
            if schema_digest in self._models:
                raise RuntimeError("Unable to register duplicate model")
            if schema_digest in self._signed_message_handlers:
                raise RuntimeError("Unable to register duplicate message handler")
            if schema_digest in protocol.signed_message_handlers:
                self._signed_message_handlers[schema_digest] = (
                    protocol.signed_message_handlers[schema_digest]
                )
            elif schema_digest in protocol.unsigned_message_handlers:
                self._unsigned_message_handlers[schema_digest] = (
                    protocol.unsigned_message_handlers[schema_digest]
                )
            elif schema_digest in protocol.state_message_handlers:
                self._state_message_handlers[schema_digest] = (
                    protocol.state_message_handlers[schema_digest]
                )
            else:
                raise RuntimeError("Unable to lookup up message handler in protocol")

            self._models[schema_digest] = protocol.models[schema_digest]

            if schema_digest in protocol.replies:
                self._replies[schema_digest] = protocol.replies[schema_digest]

        if protocol.digest is not None:
            self.protocols[protocol.digest] = protocol
            if self._ctx is not None:
                self._ctx.update_protocols(protocol)

        if publish_manifest:
            self.publish_manifest(protocol.manifest())

    def start_background_tasks(self):
        """
        Start background tasks for the agent.

        """
        # Start the interval tasks
        for func, period, state in self._interval_handlers:
            task = self._loop.create_task(_run_interval(func, state, self._ctx, period))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        # start the background message queue processor
        task = self._loop.create_task(self._process_message_queue())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # start the wallet messaging client if enabled
        if self._wallet_messaging_client is not None:
            for task in [
                self._wallet_messaging_client.poll_server(),
                self._wallet_messaging_client.process_message_queue(self._ctx),
            ]:
                new_task = self._loop.create_task(task)
                self._background_tasks.add(new_task)
                new_task.add_done_callback(self._background_tasks.discard)

    # message handling
    def on_message(
        self,
        model: Model,
        replies: type[Model] | Set[type[Model]] | None = None,
        allow_unverified: bool | None = False,
        state: Optional[str] = None,
    ):
        return self._protocol.on_message(model, replies, allow_unverified, state)

    async def _process_message_queue(self):  # noqa
        """
        Process the message queue.

        """
        while True:
            # get an element from the queue
            schema_digest, sender, message, session = await self._message_queue.get()

            # lookup the model definition
            model_class: Model = self._models.get(schema_digest)
            if model_class is None:
                self._logger.warning(
                    f"Received message with unrecognized schema digest: {schema_digest}"
                )
                continue

            context = Context(
                self._identity.address,
                self.identifier,
                self._name,
                self._storage,
                self._resolver,
                self._identity,
                self._wallet,
                self._ledger,
                self._queries,
                session=session,
                replies=self._replies,
                interval_messages=self._interval_messages,
                message_received=MsgDigest(
                    message=message, schema_digest=schema_digest
                ),
                protocols=self.protocols,
                logger=self._logger,
            )

            # parse the received message
            try:
                recovered = model_class.parse_raw(message)
            except ValidationError as ex:
                self._logger.warning(f"Unable to parse message: {ex}")
                await _send_error_message(
                    context,
                    sender,
                    ErrorMessage(
                        error=f"Message does not conform to expected schema: {ex}"
                    ),
                )
                continue

            # attempt to find the handler
            handler: MessageCallback = self._unsigned_message_handlers.get(
                schema_digest
            )
            if handler is None:
                if not is_user_address(sender):
                    is_valid = True  # always valid unless considered invalid as part of a dialogue
                    for protocol in context.protocols.values():
                        if hasattr(protocol, "rules") and protocol.is_included(
                            schema_digest
                        ):
                            state = protocol.get_current_state(session)
                            context.logger.debug(
                                "current state: "
                                f"{(protocol.models[state].__name__ if state else 'n/a')}"
                            )
                            is_valid = protocol.is_valid_message(session, schema_digest)
                            context.logger.debug(
                                f"message {self._models[schema_digest].__name__} "
                                f"allowed: {is_valid}"
                            )

                            if not is_valid:
                                context.reset_session()
                                await _send_error_message(
                                    context,
                                    sender,
                                    ErrorMessage(
                                        error=f"Unexpected message in dialogue: {message}"
                                    ),
                                )
                                break

                            if protocol.is_starter(schema_digest):
                                self._ctx.logger.debug("dialogue started")
                            elif protocol.is_ender(schema_digest):
                                self._ctx.logger.debug(
                                    "dialogue ended, cleaning up session"
                                )
                            else:
                                self._ctx.logger.debug("dialogue picked up")

                            context.dialogue = protocol.get_session(
                                session
                            )  # add current dialogue messages to context
                            protocol.add_message(
                                session_id=session,
                                message_type=self._models[schema_digest].__name__,
                                sender=sender,
                                receiver=self.address,
                                content=message,
                            )
                    if is_valid:
                        handler = self._signed_message_handlers.get(schema_digest)
                        if handler is None:  # check for stateful message handler last
                            handler, state = self._state_message_handlers.get(
                                schema_digest
                            )
                            # discuss how to handle messages for an agent that
                            # is not in the correct state
                            if state != self.state:
                                # await _send_error_message(
                                #     context,
                                #     sender,
                                #     ErrorMessage(
                                #         error="Agent not in correct state to handle message"
                                #     ),
                                # )
                                continue
                elif schema_digest in self._signed_message_handlers:
                    await _send_error_message(
                        context,
                        sender,
                        ErrorMessage(
                            error="Message must be sent from verified agent address"
                        ),
                    )
                    continue

            if handler is not None:
                try:
                    await handler(context, sender, recovered)
                except OSError as ex:
                    self._logger.exception(f"OS Error in message handler: {ex}")
                except RuntimeError as ex:
                    self._logger.exception(f"Runtime Error in message handler: {ex}")
                except Exception as ex:
                    self._logger.exception(f"Exception in message handler: {ex}")
