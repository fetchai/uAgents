import hashlib
import json
from typing import Type, Union

from pydantic import BaseModel


class Model(BaseModel):
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
