from uuid import uuid4

from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
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

host_proto = Protocol(spec=chat_protocol_spec)
picker_proto = Protocol(spec=chat_protocol_spec)


@host_proto.on_message(ChatAcknowledgement)
async def host_ack(_ctx: Context, _sender: str, _msg: ChatAcknowledgement):
    pass


@host_proto.on_message(ChatMessage)
async def host_handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    for block in msg.content:
        if not isinstance(block, MetadataContent):
            continue
        response = extract_card_response(block)
        if response is None:
            continue
        if response.cancelled:
            ctx.logger.info("Picker cancelled the card")
        elif response.selection is not None:
            ctx.logger.info("Picker selected: %s", response.selection)
        await ctx.send(sender, ChatAcknowledgement(acknowledged_msg_id=msg.msg_id))
        return

    if msg.text().strip().lower() != "menu":
        return

    await ctx.send(
        sender,
        ChatMessage(
            [
                TextContent("Choose a snack:"),
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
        ctx.logger.info("Replying with selection: %s", selection)
        await ctx.send(
            sender,
            ChatMessage(
                [
                    create_card_response_content(
                        card_id=card.card_id,
                        selection=selection,
                    )
                ]
            ),
        )
        return

    await ctx.send(sender, ChatAcknowledgement(acknowledged_msg_id=msg.msg_id))
