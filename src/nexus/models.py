import hashlib
from typing import Any, Dict

from pydantic import BaseModel


class Model(BaseModel):
    @staticmethod
    def build_schema_digest(model: "Model") -> str:
        return (
            hashlib.sha256(
                model.schema_json(indent=None, sort_keys=True).encode("utf8")
            )
            .digest()
            .hex()
        )

    @classmethod
    def parse(cls, model: Any) -> Dict[str, Any]:
        if isinstance(model, dict):
            return cls.parse_obj(model)
        else:
            return cls.parse_raw(model)


class ErrorMessage(Model):
    error: str
