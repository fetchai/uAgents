import hashlib
import json
from typing import Type, Union

from pydantic import BaseModel


class Model(BaseModel):
    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        schema = model.model_json_schema()
        digest = (
            hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf8"))
            .digest()
            .hex()
        )

        return f"model:{digest}"


class ErrorMessage(Model):
    """Error message model"""

    error: str
