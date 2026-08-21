"""
Interactive card schemas and MetadataContent helpers.

Card requests and responses are carried in ``MetadataContent`` blocks; the chat
protocol digest is unchanged. Use ``create_card_content()`` /
``create_card_response_content()`` to emit blocks and ``extract_card()`` /
``extract_card_response()`` to read them.

See ``README.md`` in this directory for usage examples and the metadata wire format.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, time
from typing import Annotated, Any, Literal

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

_SELECT_KINDS = frozenset({"select", "multiselect"})
_NO_MIN_MAX_KINDS = frozenset({"email", "phone", "select", "checkbox"})
_E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")

META_CARD_PROTOCOL_VERSION = "card_protocol_version"
META_REQUIRES_CARD_INTERACTION = "requires_card_interaction"
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


def _is_set(value: object) -> bool:
    return value is not None


def _is_non_blank(text: str) -> bool:
    return bool(text.strip())


def _normalize_non_blank_str(text: str, *, field_name: str) -> str:
    normalized = text.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _normalize_http_url(url: str, *, field_name: str) -> str:
    normalized = url.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty http:// or https:// URL")
    if not (normalized.startswith("http://") or normalized.startswith("https://")):
        raise ValueError(f"{field_name} must be an http:// or https:// URL")
    return normalized


def _normalize_optional_http_url(url: str | None, *, field_name: str) -> str | None:
    if url is None:
        return None
    return _normalize_http_url(url, field_name=field_name)


def _normalize_display_image(image: DisplayImage) -> DisplayImage:
    image.src = _normalize_http_url(image.src, field_name="src")
    return image


def _normalize_media_item(
    item: str | DisplayImage,
    *,
    field_name: str,
) -> str | DisplayImage:
    if isinstance(item, str):
        return _normalize_http_url(item, field_name=field_name)
    return _normalize_display_image(item)


def _normalize_optional_media(
    url: str | DisplayImage | None,
    *,
    field_name: str,
) -> str | DisplayImage | None:
    if url is None:
        return None
    return _normalize_media_item(url, field_name=field_name)


def _normalize_optional_medias(
    urls: str | DisplayImage | list[str | DisplayImage] | None,
    *,
    field_name: str,
) -> str | DisplayImage | list[str | DisplayImage] | None:
    if urls is None:
        return None
    if isinstance(urls, list):
        return [
            _normalize_media_item(item, field_name=f"{field_name}[{index}]")
            for index, item in enumerate(urls)
        ]
    return _normalize_media_item(urls, field_name=field_name)


def _validate_non_empty_selection(
    selection: dict, *, field_name: str = "selection"
) -> None:
    if not selection:
        raise ValueError(f"{field_name} must contain at least one key")


def _has_button_label(label: str | LabelWithIcon | None) -> bool:
    if label is None:
        return False
    if isinstance(label, str):
        return _is_non_blank(label)
    return _is_non_blank(label.label)


def _reject_if_set(value: object, *, field_name: str, kind: str) -> None:
    if value is not None:
        raise ValueError(f"{field_name} not allowed for kind={kind!r}")


def _validate_int_bounds(
    minimum: int | None,
    maximum: int | None,
    *,
    kind: str,
) -> None:
    if _is_set(minimum) and minimum < 0:
        raise ValueError(f"minimum must be >= 0 for kind={kind!r}")
    if _is_set(maximum) and kind == "multiselect" and maximum < 1:
        raise ValueError("multiselect maximum must be >= 1 when set")
    if _is_set(minimum) and _is_set(maximum) and minimum > maximum:
        raise ValueError(f"minimum must be <= maximum for kind={kind!r}")


class DisplayImage(_StrictBase):
    """Image reference with optional display metadata. Plain URL strings remain valid."""

    src: str
    alt: str | None = None
    aspect_ratio: str | None = Field(
        default=None,
        pattern=r"^\d+:\d+$",
        description='Width:height, e.g. "16:9", "3:4", "1:1"',
    )

    @model_validator(mode="after")
    def _validate_media_url(self) -> DisplayImage:
        self.src = _normalize_http_url(self.src, field_name="src")
        return self


class LabelWithIcon(_StrictBase):
    label: str
    src: str
    alt: str | None = None

    @model_validator(mode="after")
    def _validate_label_and_src(self) -> LabelWithIcon:
        self.label = _normalize_non_blank_str(self.label, field_name="label")
        self.src = _normalize_http_url(self.src, field_name="src")
        return self


class ExpandedChoice(_StrictBase):
    """Extra content the drawer shows when a sub-option choice is selected."""

    image: str | DisplayImage | list[str | DisplayImage] | None = None
    content: str | None = None
    additional_data: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_non_empty_expanded_choice(self) -> ExpandedChoice:
        if not (self.image or self.content or self.additional_data):
            raise ValueError(
                "At least one of `image`, `content`, or `additional_data` "
                "must be provided in ExpandedChoice."
            )
        self.image = _normalize_optional_medias(self.image, field_name="image")
        return self


class CtaAction(_StrictBase):
    label: str
    selection: dict
    primary: bool = False

    @model_validator(mode="after")
    def _non_empty_selection(self) -> CtaAction:
        self.label = _normalize_non_blank_str(self.label, field_name="label")
        _validate_non_empty_selection(self.selection)
        return self


class CarouselBadge(_StrictBase):
    label: str
    variant: Literal["info", "success", "warning"] | None = None


class CarouselItem(_StrictBase):
    id: str
    image: str | DisplayImage | list[str | DisplayImage] | None = None
    title: str
    subtitle: str | None = None
    badges: list[CarouselBadge] | None = None
    secondary_text: str | None = None
    primary_cta: CtaAction
    logo: str | None = None

    @model_validator(mode="after")
    def _validate_media_urls(self) -> CarouselItem:
        self.image = _normalize_optional_medias(self.image, field_name="image")
        self.logo = _normalize_optional_http_url(self.logo, field_name="logo")
        return self


class CarouselCardPayload(_StrictBase):
    title: str | None = None
    subtitle: str | None = None
    items: list[CarouselItem] = Field(min_length=1)
    style: Literal["scroll", "slide"] = "scroll"
    root_cta: CtaAction | None = None


class DetailSummaryRow(_StrictBase):
    label: str
    value: str


class DetailSubOptionChoice(_StrictBase):
    value: str
    label: str
    secondary_text: str | None = None
    expanded: ExpandedChoice | None = None


class DetailSubOptions(_StrictBase):
    name: str
    kind: Literal["radio", "select"]
    label: str
    choices: list[DetailSubOptionChoice] = Field(min_length=1)


class DetailCardPayload(_StrictBase):
    title: str
    hero_image: str | DisplayImage | list[str | DisplayImage] | None = None
    summary_rows: list[DetailSummaryRow] | None = None
    sub_options: DetailSubOptions | None = None
    ctas: list[CtaAction] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_media_urls(self) -> DetailCardPayload:
        self.hero_image = _normalize_optional_medias(
            self.hero_image, field_name="hero_image"
        )
        return self


class FormFieldOption(_StrictBase):
    value: str
    label: str


InputOption = FormFieldOption


class InputFieldBase(_StrictBase):
    name: str
    kind: Literal[
        "text",
        "number",
        "email",
        "select",
        "checkbox",
        "date",
        "time",
        "multiselect",
        "phone",
    ]
    label: str
    required: bool = False
    options: list[FormFieldOption] | None = None
    placeholder: str | None = None
    default: str | None = None
    description: str | None = None
    minimum: int | date | time | None = None
    maximum: int | date | time | None = None
    multiline: bool | None = None

    @model_validator(mode="after")
    def _validate_kind_rules(self) -> InputFieldBase:
        if self.kind in _SELECT_KINDS:
            if not self.options:
                raise ValueError(f"{self.kind} requires non-empty options")
        elif self.options is not None:
            raise ValueError(f"options not allowed for kind={self.kind!r}")

        if self.kind != "text":
            _reject_if_set(self.multiline, field_name="multiline", kind=self.kind)

        if self.kind in _NO_MIN_MAX_KINDS:
            _reject_if_set(self.minimum, field_name="minimum", kind=self.kind)
            _reject_if_set(self.maximum, field_name="maximum", kind=self.kind)
        elif self.kind == "text":
            if _is_set(self.minimum) and not isinstance(self.minimum, int):
                raise ValueError("minimum for text must be an integer (length)")
            if _is_set(self.maximum) and not isinstance(self.maximum, int):
                raise ValueError("maximum for text must be an integer (length)")
            _validate_int_bounds(
                self.minimum if isinstance(self.minimum, int) else None,
                self.maximum if isinstance(self.maximum, int) else None,
                kind=self.kind,
            )
        elif self.kind == "number":
            if _is_set(self.minimum) and not isinstance(self.minimum, int):
                raise ValueError("minimum for number must be an integer")
            if _is_set(self.maximum) and not isinstance(self.maximum, int):
                raise ValueError("maximum for number must be an integer")
            _validate_int_bounds(
                self.minimum if isinstance(self.minimum, int) else None,
                self.maximum if isinstance(self.maximum, int) else None,
                kind=self.kind,
            )
        elif self.kind == "date":
            if _is_set(self.minimum) and not isinstance(self.minimum, date):
                raise ValueError("minimum for date must be an ISO date (YYYY-MM-DD)")
            if _is_set(self.maximum) and not isinstance(self.maximum, date):
                raise ValueError("maximum for date must be an ISO date (YYYY-MM-DD)")
            if (
                isinstance(self.minimum, date)
                and isinstance(self.maximum, date)
                and self.minimum > self.maximum
            ):
                raise ValueError("minimum must be <= maximum for kind='date'")
        elif self.kind == "time":
            if _is_set(self.minimum) and not isinstance(self.minimum, time):
                raise ValueError(
                    "minimum for time must be an ISO time (HH:MM or HH:MM:SS)"
                )
            if _is_set(self.maximum) and not isinstance(self.maximum, time):
                raise ValueError(
                    "maximum for time must be an ISO time (HH:MM or HH:MM:SS)"
                )
            if (
                isinstance(self.minimum, time)
                and isinstance(self.maximum, time)
                and self.minimum > self.maximum
            ):
                raise ValueError("minimum must be <= maximum for kind='time'")
        elif self.kind == "multiselect":
            if _is_set(self.minimum) and not isinstance(self.minimum, int):
                raise ValueError(
                    "minimum for multiselect must be an integer (selection count)"
                )
            if _is_set(self.maximum) and not isinstance(self.maximum, int):
                raise ValueError(
                    "maximum for multiselect must be an integer (selection count)"
                )
            _validate_int_bounds(
                self.minimum if isinstance(self.minimum, int) else None,
                self.maximum if isinstance(self.maximum, int) else None,
                kind=self.kind,
            )
            if self.required and _is_set(self.minimum) and self.minimum < 1:
                raise ValueError(
                    "required multiselect fields need minimum >= 1 when set"
                )

        self._validate_default()
        return self

    def _validate_default(self) -> None:
        if self.default is None:
            return

        if self.kind == "phone":
            if not _E164_PATTERN.match(self.default):
                raise ValueError(
                    "phone default must be E.164 format "
                    "(+[country][number], max 15 digits)"
                )
            return

        if self.kind == "date":
            try:
                date.fromisoformat(self.default)
            except ValueError as exc:
                raise ValueError("date default must be ISO date YYYY-MM-DD") from exc
            return

        if self.kind == "time":
            try:
                time.fromisoformat(self.default)
            except ValueError as exc:
                raise ValueError(
                    "time default must be ISO time HH:MM or HH:MM:SS"
                ) from exc
            return

        if self.kind == "checkbox":
            if self.default not in ("true", "false"):
                raise ValueError("checkbox default must be 'true' or 'false'")
            return

        if self.kind == "number":
            try:
                int(self.default)
            except ValueError:
                try:
                    float(self.default)
                except ValueError as exc:
                    raise ValueError("number default must be a numeric string") from exc
            return

        if self.kind == "select":
            if self.options and self.default not in {
                option.value for option in self.options
            }:
                raise ValueError("select default must match an option value")
            return

        if self.kind == "multiselect":
            try:
                values = json.loads(self.default)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "multiselect default must be a JSON array of option values"
                ) from exc
            if not isinstance(values, list) or not all(
                isinstance(value, str) for value in values
            ):
                raise ValueError("multiselect default must be a JSON array of strings")
            if self.options:
                allowed = {option.value for option in self.options}
                if not all(value in allowed for value in values):
                    raise ValueError(
                        "multiselect default values must match option values"
                    )


class FormField(InputFieldBase):
    """Form card field — shares validation with element-tree ``InputNode``."""


class FormCardPayload(_StrictBase):
    title: str | None = None
    fields: list[FormField] = Field(min_length=1)
    submit_cta: CtaAction
    cancel_cta: CtaAction | None = None


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
    aspect_ratio: str | None = Field(
        default=None,
        pattern=r"^\d+:\d+$",
        description='Width:height, e.g. "16:9", "3:4", "1:1"',
    )

    @model_validator(mode="after")
    def _validate_media_url(self) -> ImageNode:
        self.src = _normalize_http_url(self.src, field_name="src")
        return self


class VideoNode(_StrictBase):
    type: Literal["video"]
    src: str
    alt: str | None = None
    aspect_ratio: str | None = Field(
        default=None,
        pattern=r"^\d+:\d+$",
        description='Width:height, e.g. "16:9", "3:4", "1:1"',
    )

    @model_validator(mode="after")
    def _validate_media_url(self) -> VideoNode:
        self.src = _normalize_http_url(self.src, field_name="src")
        return self


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
    gap: int | None = Field(default=None, ge=1)
    children: list[ElementTreeNode] = Field(min_length=1)


class ButtonAction(_StrictBase):
    selection: dict | None = None
    redirect: str | None = None
    bypass_required_validation: bool | None = Field(
        default=None,
        description=(
            "When true, the UI may activate this button without required input/choice_grid "
            "fields being filled (e.g. Cancel). When false or omitted, required fields "
            "must be satisfied first. Enforced client-side."
        ),
    )

    @model_validator(mode="after")
    def _selection_or_redirect_required(self) -> ButtonAction:
        has_selection = self.selection is not None
        if self.redirect is not None:
            stripped = self.redirect.strip()
            self.redirect = (
                _normalize_http_url(stripped, field_name="redirect") if stripped else None
            )
        has_redirect = self.redirect is not None
        if not has_selection and not has_redirect:
            raise ValueError("action requires at least one of selection or redirect")
        if has_selection:
            _validate_non_empty_selection(self.selection)
        return self


class ButtonNode(_StrictBase):
    type: Literal["button"]
    label: str | LabelWithIcon | None = None
    image: DisplayImage | None = None
    primary: bool = False
    action: ButtonAction

    @model_validator(mode="after")
    def _label_or_image_required(self) -> ButtonNode:
        if isinstance(self.label, str):
            self.label = _normalize_non_blank_str(self.label, field_name="label")
        if not _has_button_label(self.label) and self.image is None:
            raise ValueError("button requires at least one of label or image")
        return self


class InputNode(InputFieldBase):
    type: Literal["input"]


class ListItem(_StrictBase):
    children: list[ElementTreeNode] = Field(min_length=1)
    action: ButtonAction | None = None


class ListNode(_StrictBase):
    type: Literal["list"]
    items: list[ListItem] = Field(min_length=1)


class ChoiceGridChoice(_StrictBase):
    value: str
    label: str
    image: str | DisplayImage | None = None

    @model_validator(mode="after")
    def _validate_media_url(self) -> ChoiceGridChoice:
        self.image = _normalize_optional_media(self.image, field_name="image")
        return self


class ChoiceGridNode(_StrictBase):
    type: Literal["choice_grid"]
    name: str
    choices: list[ChoiceGridChoice] = Field(min_length=1)
    multi: bool = False


ElementTreeNode = Annotated[
    TextNode
    | HeadingNode
    | ImageNode
    | VideoNode
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
        META_REQUIRES_CARD_INTERACTION: "true",
        META_CARD_KIND: card_kind,
        META_CARD_PAYLOAD: card.payload.model_dump_json(exclude_none=True),
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
