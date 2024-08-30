import hashlib
import json
from dataclasses import dataclass
from typing import Literal, Type, Union

from pydantic import BaseModel

BASE_CLASSES = Literal["str", "int", "float", "bool", "list", "dict", "object"]


@dataclass
class PropertyField:
    types: list[BASE_CLASSES]
    title: str
    required: bool
    description: str
    default: str


@dataclass
class Schema:
    title: str
    description: str
    type: BASE_CLASSES
    properties: dict[str, PropertyField]
    required: list[str]


# slightly different schema V
#                           V
# pydantic schema > custom schema (JSON Schema similiar) > calculate digest


class Model(BaseModel):
    _schema = None

    # This is a WIP - please ignore for now
    @classmethod
    def build_schema(cls) -> dict:
        """
        Build a schema for a model.

        Targeting JSON schema format. similar but not the same
        """
        # enforce Fetch specification
        schema = cls.model_json_schema()

        # cls.model_fields_set

        schema.pop("description", None)
        schema.pop("type", None)
        if "required" in schema and isinstance(schema["required"], list):
            schema["required"].sort()
        # for field in ...:
        #     pass
        return schema

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        """Build a unique identifier for a model schema."""
        # schema = model.build_schema()

        schema = model.model_json_schema()
        if "required" in schema and isinstance(schema["required"], list):
            schema["required"].sort()
        dump = json.dumps(schema, indent=None, sort_keys=True)
        digest = hashlib.sha256(dump.encode("utf8")).digest().hex()

        return f"model:{digest}"


class ErrorMessage(Model):
    """Error message model"""

    error: str
