import hashlib
from typing import Any, Type, Union

from pydantic.v1 import BaseModel, Field  # noqa


# reverting back to pydantic v1 BaseModel for backwards compatibility
class Model(BaseModel):
    @classmethod
    def model_json_schema(cls) -> str:
        return cls.schema_json()

    def model_dump_json(self) -> str:
        return self.json()

    @classmethod
    def model_validate_json(cls, obj: Any) -> "Model":
        return cls.parse_raw(obj)

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        schema = model.schema_json(indent=None, sort_keys=True)
        digest = hashlib.sha256(schema.encode("utf8")).digest().hex()

        return f"model:{digest}"


class ErrorMessage(Model):
    """Error message model"""

    error: str
