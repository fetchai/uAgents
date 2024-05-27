import hashlib
import json
from typing import Type, Union

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


class ExcludeMetadataGenerateJsonSchema(GenerateJsonSchema):
    def generate(self, schema, mode="validation") -> JsonSchemaValue:
        json_schema = super().generate(schema, mode=mode)
        if "description" in json_schema:
            json_schema.pop("description")
        if "properties" in json_schema:
            for prop in json_schema["properties"]:
                json_schema["properties"][prop].pop("description", None)
        # When the same fields are defined in differend order, 'sort_keys' will not
        # consider the "required" entry, because it is a list.
        # TODO extend this to generically find any list in the dict and sort it
        if "required" in json_schema:
            json_schema["required"].sort()
        return json_schema


class Model(BaseModel):
    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        schema = model.model_json_schema(
            schema_generator=ExcludeMetadataGenerateJsonSchema
        )
        digest = (
            hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf8"))
            .digest()
            .hex()
        )

        return f"model:{digest}"


class ErrorMessage(Model):
    """Error message model"""

    error: str
