import hashlib
from typing import Type, Union

from pydantic import BaseModel


class Model(BaseModel):
    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        """

        :rtype: object
        """
        return (
            hashlib.sha256(
                model.schema_json(indent=None, sort_keys=True).encode("utf8")
            )
            .digest()
            .hex()
        )


class ErrorMessage(Model):
    error: str
