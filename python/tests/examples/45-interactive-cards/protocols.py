import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    MetadataContent,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.contrib.protocols.chat.cards import (
    CarouselCardPayload,
    CarouselItem,
    CtaAction,
    create_card_content,
    create_card_response_content,
    extract_card,
    extract_card_response,
)

MENU_CAROUSEL = CarouselCardPayload(
    title="Snack menu",
    items=[
        CarouselItem(
            id="apple",
            title="Apple",
            subtitle="Fresh and crisp",
            primary_cta=CtaAction(label="Order", selection={"item_id": "apple"}),
        ),
        CarouselItem(
            id="banana",
            title="Banana",
            subtitle="Rich in potassium",
            primary_cta=CtaAction(label="Order", selection={"item_id": "banana"}),
        ),
    ],
)

MENU_INTRO = "Pick a snack from the menu:"

host_proto = Protocol(spec=chat_protocol_spec)
picker_proto = Protocol(spec=chat_protocol_spec)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _chat(content: list) -> ChatMessage:
    return ChatMessage(timestamp=_now(), msg_id=uuid4(), content=content)


def _parse_ui_selection(text: str) -> dict[str, Any] | None:
    """ASI UI follow-up: @agent… {"item_id":"apple","approved":true}"""
    start = text.find("{")
    if start == -1:
        return None
    try:
        data = json.loads(text[start:])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    item_id = data.get("item_id")
    if not item_id:
        return None
    return {"item_id": str(item_id)}


async def _confirm_order(ctx: Context, sender: str, selection: dict[str, Any]) -> None:
    item_id = selection["item_id"]
    ctx.logger.info("Order confirmed: %s", item_id)
    await ctx.send(
        sender,
        _chat(
            [
                TextContent(
                    type="text",
                    text=f"Got it — ordering {item_id} for you.",
                ),
                EndSessionContent(type="end-session"),
            ]
        ),
    )


@host_proto.on_message(ChatAcknowledgement)
async def host_ack(_ctx: Context, _sender: str, _msg: ChatAcknowledgement):
    pass


@host_proto.on_message(ChatMessage)
async def host_handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=_now(), acknowledged_msg_id=msg.msg_id),
    )

    text = msg.text()

    for block in msg.content:
        if not isinstance(block, MetadataContent):
            continue
        response = extract_card_response(block)
        if response and response.selection:
            await _confirm_order(ctx, sender, response.selection)
            return

    selection = _parse_ui_selection(text)
    if selection:
        await _confirm_order(ctx, sender, selection)
        return

    if "menu" in text.lower():
        ctx.logger.info("Sending menu card")
        await ctx.send(
            sender,
            _chat(
                [
                    TextContent(type="text", text=MENU_INTRO),
                    create_card_content(MENU_CAROUSEL, card_id=uuid4()),
                ]
            ),
        )


@picker_proto.on_message(ChatAcknowledgement)
async def picker_ack(_ctx: Context, _sender: str, _msg: ChatAcknowledgement):
    pass


@picker_proto.on_message(ChatMessage)
async def picker_handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    for block in msg.content:
        if not isinstance(block, MetadataContent):
            continue
        card = extract_card(block)
        if card is None:
            continue
        payload = card.payload
        if not isinstance(payload, CarouselCardPayload) or not payload.items:
            ctx.logger.warning("Expected a carousel card with at least one item")
            return
        selection = payload.items[0].primary_cta.selection
        await ctx.send(
            sender,
            _chat(
                [
                    create_card_response_content(
                        card_id=card.card_id,
                        selection=selection,
                    )
                ]
            ),
        )
        return

    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=_now(), acknowledged_msg_id=msg.msg_id),
    )
