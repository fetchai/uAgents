import hashlib
from typing import Type, Union

from pydantic import BaseModel


class Model(BaseModel):
    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        digest = (
            hashlib.sha256(
                model.schema_json(indent=None, sort_keys=True).encode("utf8")
            )
            .digest()
            .hex()
        )

        return f"model:{digest}"


class ErrorMessage(Model):
    error: str
