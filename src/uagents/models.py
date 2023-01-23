import hashlib

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


class ErrorMessage(Model):
    error: str
