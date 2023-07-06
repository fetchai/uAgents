import hashlib
from typing import Type, Union, Dict
import json
from pydantic import BaseModel


class Model(BaseModel):
    @staticmethod
    def remove_descriptions(schema: Dict[str, Dict[str, str]]):
        fields_with_descr = []
        if not "properties" in schema:
            return
        for field_name, field_props in schema["properties"].items():
            if "description" in field_props:
                fields_with_descr.append(field_name)

        for field_name in fields_with_descr:
            del schema["properties"][field_name]["description"]

        if "definitions" in schema:
            for definition in schema["definitions"].values():
                Model.remove_descriptions(definition)

    @classmethod
    def schema_json_no_descr(cls) -> str:
        orig_schema = json.loads(cls.schema_json(indent=None, sort_keys=True))
        Model.remove_descriptions(orig_schema)
        return json.dumps(orig_schema)

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        digest = (
            hashlib.sha256(model.schema_json_no_descr().encode("utf-8")).digest().hex()
        )
        return f"model:{digest}"


class ErrorMessage(Model):
    error: str
