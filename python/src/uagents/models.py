import hashlib
from typing import Type, Union

from pydantic.v1 import BaseModel


# reverting back to pydantic.v1 BaseModel for backwards compatibility
class Model(BaseModel):
    @classmethod
    def model_json_schema(cls) -> str:
        return cls.schema_json(indent=None, sort_keys=True)

    def model_dump_json(self) -> str:
        return self.json(indent=None, sort_keys=True)

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        schema = model.schema_json(indent=None, sort_keys=True)
        digest = hashlib.sha256(schema.encode("utf8")).digest().hex()

        return f"model:{digest}"


class ErrorMessage(Model):
    """Error message model"""

    error: str
