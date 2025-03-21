import hashlib
from typing import Any

from pydantic.v1 import BaseModel, Field  # noqa
from typing_extensions import Self


# reverting back to pydantic v1 BaseModel for backwards compatibility
class Model(BaseModel):
    @classmethod
    def model_json_schema(cls) -> str:
        return cls.schema_json()

    def model_dump_json(self) -> str:
        return self.json()

    def model_dump(self) -> dict[str, Any]:
        return self.dict()

    @classmethod
    def model_validate_json(cls, obj: Any) -> Self:
        return cls.parse_raw(obj)

    @classmethod
    def model_validate(cls, obj: dict[str, Any] | Self) -> Self:
        return cls.parse_obj(obj)

    @staticmethod
    def build_schema_digest(model: BaseModel | type[BaseModel]) -> str:
        schema = model.schema_json(indent=None, sort_keys=True)
        digest = hashlib.sha256(schema.encode("utf8")).digest().hex()

        return f"model:{digest}"


class ErrorMessage(Model):
    """Error message model"""

    error: str


ERROR_MESSAGE_DIGEST = Model.build_schema_digest(ErrorMessage)
