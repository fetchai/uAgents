"""
Interactive card schemas and MetadataContent helpers.

Card requests and responses are carried in ``MetadataContent`` blocks; the chat
protocol digest is unchanged. Use ``create_card_content()`` /
``create_card_response_content()`` to emit blocks and ``extract_card()`` /
``extract_card_response()`` to read them.

See ``README.md`` in this directory for usage examples and the metadata wire format.
"""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from uagents_core.contrib.protocols.chat import MetadataContent

_logger = logging.getLogger(__name__)

CARD_PROTOCOL_VERSION = "1"
MAX_ELEMENT_TREE_DEPTH = 8

META_CARD_PROTOCOL_VERSION = "card_protocol_version"
META_CARD_ID = "card_id"
META_CARD_KIND = "card_kind"
META_CARD_PAYLOAD = "card_payload"
META_IS_TERMINAL = "is_terminal"
META_PREFERRED_DRAWER_WIDTH_PX = "preferred_drawer_width_px"
META_TEXT = "text"
META_SELECTION = "selection"
META_CANCELLED = "cancelled"

SelectionValue = str | int | float | bool


class _StrictBase(BaseModel):
    """Reject unknown attributes by default — tighter than agent-friendly defaults."""

    model_config = ConfigDict(extra="forbid")


class CtaAction(_StrictBase):
    label: str
    selection: dict
    primary: bool = False


class CarouselBadge(_StrictBase):
    label: str
    variant: Literal["info", "success", "warning"] | None = None


class CarouselItem(_StrictBase):
    id: str
    image: str | None = None
    title: str
    subtitle: str | None = None
    badges: list[CarouselBadge] | None = None
    secondary_text: str | None = None
    primary_cta: CtaAction


class CarouselCardPayload(_StrictBase):
    title: str | None = None
    subtitle: str | None = None
    items: list[CarouselItem] = Field(min_length=1)


class DetailSummaryRow(_StrictBase):
    label: str
    value: str


class DetailSubOptionChoice(_StrictBase):
    value: str
    label: str
    secondary_text: str | None = None


class DetailSubOptions(_StrictBase):
    name: str
    kind: Literal["radio", "select"]
    label: str
    choices: list[DetailSubOptionChoice] = Field(min_length=1)


class DetailCardPayload(_StrictBase):
    title: str
    hero_image: str | None = None
    summary_rows: list[DetailSummaryRow] | None = None
    sub_options: DetailSubOptions | None = None
    ctas: list[CtaAction] = Field(min_length=1)


class FormFieldOption(_StrictBase):
    value: str
    label: str


class FormField(_StrictBase):
    name: str
    kind: Literal["text", "number", "email", "select", "checkbox"]
    label: str
    required: bool = False
    options: list[FormFieldOption] | None = None
    placeholder: str | None = None

    @model_validator(mode="after")
    def _select_requires_options(self) -> FormField:
        if self.kind == "select" and not self.options:
            raise ValueError("select fields require non-empty options")
        return self


class FormCardPayload(_StrictBase):
    title: str | None = None
    fields: list[FormField] = Field(min_length=1)
    submit_cta: CtaAction


class ReviewSummaryRow(_StrictBase):
    label: str
    value: str


class ReviewCardPayload(_StrictBase):
    title: str
    summary_rows: list[ReviewSummaryRow] = Field(min_length=1)
    approve_cta: CtaAction
    reject_cta: CtaAction | None = None


# Element-tree primitives (card_kind="custom")


class TextNode(_StrictBase):
    type: Literal["text"]
    value: str
    style: Literal["body", "muted", "emphasis"] | None = None


class HeadingNode(_StrictBase):
    type: Literal["heading"]
    value: str
    level: Literal[1, 2, 3] = 2


class ImageNode(_StrictBase):
    type: Literal["image"]
    src: str
    alt: str | None = None
    aspect_ratio: str | None = None


class BadgeNode(_StrictBase):
    type: Literal["badge"]
    label: str
    variant: Literal["info", "success", "warning"] | None = None


class DividerNode(_StrictBase):
    type: Literal["divider"]


class SectionNode(_StrictBase):
    type: Literal["section"]
    title: str | None = None
    subtitle: str | None = None
    children: list[ElementTreeNode] = Field(min_length=1)


class GroupNode(_StrictBase):
    type: Literal["group"]
    direction: Literal["row", "column"]
    gap: int | None = None
    children: list[ElementTreeNode] = Field(min_length=1)


class ButtonAction(_StrictBase):
    selection: dict


class ButtonNode(_StrictBase):
    type: Literal["button"]
    label: str
    primary: bool = False
    action: ButtonAction


class InputOption(_StrictBase):
    value: str
    label: str


class InputNode(_StrictBase):
    type: Literal["input"]
    name: str
    kind: Literal["text", "number", "email", "select", "checkbox"]
    label: str
    required: bool = False
    options: list[InputOption] | None = None
    placeholder: str | None = None

    @model_validator(mode="after")
    def _select_requires_options(self) -> InputNode:
        if self.kind == "select" and not self.options:
            raise ValueError("select inputs require non-empty options")
        return self


class ListItem(_StrictBase):
    children: list[ElementTreeNode] = Field(min_length=1)
    action: ButtonAction | None = None


class ListNode(_StrictBase):
    type: Literal["list"]
    items: list[ListItem] = Field(min_length=1)


class ChoiceGridChoice(_StrictBase):
    value: str
    label: str
    image: str | None = None


class ChoiceGridNode(_StrictBase):
    type: Literal["choice_grid"]
    name: str
    choices: list[ChoiceGridChoice] = Field(min_length=1)
    multi: bool = False


ElementTreeNode = Annotated[
    TextNode
    | HeadingNode
    | ImageNode
    | BadgeNode
    | DividerNode
    | SectionNode
    | GroupNode
    | ButtonNode
    | InputNode
    | ListNode
    | ChoiceGridNode,
    Field(discriminator="type"),
]


def _measure_depth(node: BaseModel, current: int = 1) -> int:
    """Maximum nesting depth from ``node``. The root counts as depth 1."""
    children: list[BaseModel] = []
    if isinstance(node, (SectionNode, GroupNode)):
        children = list(node.children)
    elif isinstance(node, ListNode):
        for item in node.items:
            children.extend(item.children)
    if not children:
        return current
    return max(_measure_depth(child, current + 1) for child in children)


class CustomCardPayload(_StrictBase):
    root: ElementTreeNode

    @model_validator(mode="after")
    def _enforce_depth(self) -> CustomCardPayload:
        depth = _measure_depth(self.root)
        if depth > MAX_ELEMENT_TREE_DEPTH:
            raise ValueError(
                f"element tree depth {depth} exceeds "
                f"MAX_ELEMENT_TREE_DEPTH={MAX_ELEMENT_TREE_DEPTH}"
            )
        return self


# Resolve forward references now that ElementTreeNode is defined.
SectionNode.model_rebuild()
GroupNode.model_rebuild()
ListItem.model_rebuild()
CustomCardPayload.model_rebuild()


KNOWN_CARD_KIND_SCHEMAS: dict[str, type[BaseModel]] = {
    "carousel": CarouselCardPayload,
    "detail": DetailCardPayload,
    "form": FormCardPayload,
    "review": ReviewCardPayload,
    "custom": CustomCardPayload,
}


def validate_card_payload(card_kind: str, payload: dict) -> BaseModel:
    """
    Validate ``payload`` against the schema for ``card_kind``.

    Raises ``ValidationError`` for shape mismatches and ``ValueError`` for
    unknown ``card_kind`` values.
    """
    schema = KNOWN_CARD_KIND_SCHEMAS.get(card_kind)
    if schema is None:
        raise ValueError(f"unknown card_kind: {card_kind!r}")
    return schema.model_validate(payload)


def validate_card_payload_json(card_kind: str, payload_json: str | bytes) -> BaseModel:
    """
    Validate a JSON ``card_payload`` string against the schema for ``card_kind``.

    Raises ``ValidationError`` for shape mismatches and ``ValueError`` for
    unknown ``card_kind`` values.
    """
    schema = KNOWN_CARD_KIND_SCHEMAS.get(card_kind)
    if schema is None:
        raise ValueError(f"unknown card_kind: {card_kind!r}")
    return schema.model_validate_json(payload_json)


_selection_adapter: TypeAdapter[dict[str, SelectionValue]] = TypeAdapter(
    dict[str, SelectionValue]
)


CardPayload = (
    CarouselCardPayload
    | DetailCardPayload
    | FormCardPayload
    | ReviewCardPayload
    | CustomCardPayload
)

_PAYLOAD_KIND_BY_TYPE: dict[type[BaseModel], str] = {
    CarouselCardPayload: "carousel",
    DetailCardPayload: "detail",
    FormCardPayload: "form",
    ReviewCardPayload: "review",
    CustomCardPayload: "custom",
}


def card_kind_for_payload(payload: CardPayload) -> str:
    """Return the ``card_kind`` string for a validated payload instance."""
    return _PAYLOAD_KIND_BY_TYPE[type(payload)]


class Card(BaseModel):
    """A card-interaction request (not a chat protocol content type)."""

    model_config = ConfigDict(extra="forbid")

    card_id: UUID4 | None = None
    payload: CardPayload
    is_terminal: bool = False
    preferred_drawer_width_px: int | None = None


class CardResponse(BaseModel):
    """A card-interaction response (not a chat protocol content type)."""

    model_config = ConfigDict(extra="forbid")

    card_id: UUID4 | None = None
    text: str | None = None
    selection: dict[str, SelectionValue] | None = None
    cancelled: bool = False


def _protocol_version(metadata: dict[str, str]) -> str | None:
    return metadata.get(META_CARD_PROTOCOL_VERSION)


def _is_card_protocol_block(metadata: dict[str, str]) -> bool:
    return _protocol_version(metadata) == CARD_PROTOCOL_VERSION


def _parse_card_id(raw: str | None) -> UUID4 | None:
    if raw is None:
        return None
    return TypeAdapter(UUID4).validate_python(raw)


def _parse_selection_json(raw: str) -> dict[str, SelectionValue] | None:
    try:
        return _selection_adapter.validate_json(raw)
    except ValidationError:
        return None


def create_card_content(
    payload: CardPayload,
    *,
    card_id: UUID4 | None = None,
    is_terminal: bool = False,
    preferred_drawer_width_px: int | None = None,
) -> MetadataContent:
    """Build a card-interaction request as ``MetadataContent`` for ``ChatMessage``."""
    card = Card(
        card_id=card_id,
        payload=payload,
        is_terminal=is_terminal,
        preferred_drawer_width_px=preferred_drawer_width_px,
    )
    card_kind = card_kind_for_payload(card.payload)
    metadata: dict[str, str] = {
        META_CARD_PROTOCOL_VERSION: CARD_PROTOCOL_VERSION,
        META_CARD_KIND: card_kind,
        META_CARD_PAYLOAD: card.payload.model_dump_json(),
    }
    if card.card_id is not None:
        metadata[META_CARD_ID] = str(card.card_id)
    if card.is_terminal:
        metadata[META_IS_TERMINAL] = "true"
    if card.preferred_drawer_width_px is not None:
        metadata[META_PREFERRED_DRAWER_WIDTH_PX] = str(card.preferred_drawer_width_px)
    return MetadataContent(metadata=metadata)


def create_card_response_content(
    *,
    card_id: UUID4 | None = None,
    text: str | None = None,
    selection: dict[str, SelectionValue] | None = None,
    cancelled: bool = False,
) -> MetadataContent:
    """Build a card-interaction response as ``MetadataContent`` for ``ChatMessage``."""
    response = CardResponse(
        card_id=card_id,
        text=text,
        selection=selection,
        cancelled=cancelled,
    )
    metadata: dict[str, str] = {META_CARD_PROTOCOL_VERSION: CARD_PROTOCOL_VERSION}
    if response.card_id is not None:
        metadata[META_CARD_ID] = str(response.card_id)
    if response.text is not None:
        metadata[META_TEXT] = response.text
    if response.selection is not None:
        metadata[META_SELECTION] = _selection_adapter.dump_json(
            response.selection
        ).decode()
    if response.cancelled:
        metadata[META_CANCELLED] = "true"
    return MetadataContent(metadata=metadata)


def extract_card(content: MetadataContent) -> Card | None:
    """Return a validated ``Card`` request, or ``None`` if ``content`` is not one."""
    metadata = content.metadata
    if not _is_card_protocol_block(metadata):
        return None
    if META_CARD_KIND not in metadata:
        return None

    card_kind = metadata[META_CARD_KIND]
    card_payload_raw = metadata.get(META_CARD_PAYLOAD)
    if card_payload_raw is None:
        _logger.warning("card request metadata missing card_payload")
        return None

    try:
        payload = validate_card_payload_json(card_kind, card_payload_raw)
    except (ValueError, ValidationError):
        _logger.warning("card request card_payload failed validation", exc_info=True)
        return None

    is_terminal = metadata.get(META_IS_TERMINAL) == "true"

    width: int | None = None
    width_raw = metadata.get(META_PREFERRED_DRAWER_WIDTH_PX)
    if width_raw is not None:
        try:
            width = int(width_raw)
        except ValueError:
            _logger.warning("card request has invalid preferred_drawer_width_px")
            return None

    try:
        parsed_card_id = _parse_card_id(metadata.get(META_CARD_ID))
    except ValidationError:
        _logger.warning("card request has invalid card_id")
        return None

    return Card(
        card_id=parsed_card_id,
        payload=payload,
        is_terminal=is_terminal,
        preferred_drawer_width_px=width,
    )


def extract_card_response(content: MetadataContent) -> CardResponse | None:
    """Return a validated ``CardResponse``, or ``None`` if ``content`` is not one."""
    metadata = content.metadata
    if not _is_card_protocol_block(metadata):
        return None
    if META_CARD_KIND in metadata:
        return None

    selection: dict[str, SelectionValue] | None = None
    selection_raw = metadata.get(META_SELECTION)
    if selection_raw is not None:
        selection = _parse_selection_json(selection_raw)
        if selection is None:
            _logger.warning("card response metadata has invalid selection JSON")
            return None

    try:
        parsed_card_id = _parse_card_id(metadata.get(META_CARD_ID))
    except ValidationError:
        _logger.warning("card response has invalid card_id")
        return None

    return CardResponse(
        card_id=parsed_card_id,
        text=metadata.get(META_TEXT),
        selection=selection,
        cancelled=metadata.get(META_CANCELLED) == "true",
    )
