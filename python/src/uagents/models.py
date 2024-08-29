import hashlib
import json
from typing import Literal, Type, Union

from pydantic import BaseModel

BASE_CLASSES = Literal["str", "int", "float", "bool", "list", "dict", "object"]


class PropertyField:
    types: list[BASE_CLASSES]
    title: str
    required: bool
    description: str
    default: str


class Model(BaseModel):
    # This is a WIP - please ignore for now
    @classmethod
    def build_schema(cls) -> dict:
        """Build a schema for a model."""
        schema = cls.model_json_schema()
        schema.pop("description", None)
        schema.pop("type", None)
        if "required" in schema and isinstance(schema["required"], list):
            schema["required"].sort()
        return schema

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        """Build a unique identifier for a model schema."""
        schema = model.model_json_schema()
        if "required" in schema and isinstance(schema["required"], list):
            schema["required"].sort()
        dump = json.dumps(schema, indent=None, sort_keys=True)
        digest = hashlib.sha256(dump.encode("utf8")).digest().hex()

        return f"model:{digest}"


class ErrorMessage(Model):
    """Error message model"""

    error: str
